import re
from collections import defaultdict

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import Message, Room

USERNAME_RE = re.compile(r"^[\w .-]{2,32}$")
SLUG_RE = re.compile(r"^[-a-zA-Z0-9_]{1,64}$")

# Process-local presence for the in-memory demo channel layer.
ROOM_PRESENCE: dict[str, set[str]] = defaultdict(set)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.room_slug = self.scope["url_route"]["kwargs"]["room_slug"]
        if not SLUG_RE.match(self.room_slug):
            await self.close()
            return

        self.room = await self.get_room(self.room_slug)
        if self.room is None:
            await self.close()
            return

        self.room_group = f"chat_{self.room_slug}"
        self.username = None

        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

        history = await self.get_history(self.room)
        await self.send_json({"type": "history", "messages": history})

    async def disconnect(self, close_code):
        if hasattr(self, "room_group"):
            await self.channel_layer.group_discard(self.room_group, self.channel_name)
            if self.username:
                ROOM_PRESENCE[self.room_slug].discard(self.username)
                await self.channel_layer.group_send(
                    self.room_group,
                    {
                        "type": "presence.event",
                        "event": "leave",
                        "username": self.username,
                        "users": sorted(ROOM_PRESENCE[self.room_slug]),
                    },
                )

    async def receive_json(self, content, **kwargs):
        event_type = content.get("type")

        if event_type == "join":
            await self.handle_join(content)
        elif event_type == "chat_message":
            await self.handle_chat_message(content)

    async def handle_join(self, content):
        username = (content.get("username") or "").strip()
        if not USERNAME_RE.match(username):
            await self.send_json(
                {
                    "type": "error",
                    "message": "Display name must be 2–32 characters (letters, numbers, spaces, . - _).",
                }
            )
            return

        self.username = username
        ROOM_PRESENCE[self.room_slug].add(username)
        users = sorted(ROOM_PRESENCE[self.room_slug])
        await self.channel_layer.group_send(
            self.room_group,
            {
                "type": "presence.event",
                "event": "join",
                "username": self.username,
                "users": users,
            },
        )

    async def handle_chat_message(self, content):
        if not self.username:
            await self.send_json({"type": "error", "message": "Join with a display name first."})
            return

        text = (content.get("message") or "").strip()
        if not text or len(text) > 1000:
            return

        message = await self.save_message(self.room, self.username, text)
        await self.channel_layer.group_send(
            self.room_group,
            {
                "type": "chat.message",
                "id": message["id"],
                "username": message["username"],
                "message": message["content"],
                "created_at": message["created_at"],
            },
        )

    async def chat_message(self, event):
        await self.send_json(
            {
                "type": "chat_message",
                "id": event["id"],
                "username": event["username"],
                "message": event["message"],
                "created_at": event["created_at"],
            }
        )

    async def presence_event(self, event):
        await self.send_json(
            {
                "type": "presence",
                "event": event["event"],
                "username": event["username"],
                "users": event.get("users", []),
            }
        )

    @database_sync_to_async
    def get_room(self, slug):
        try:
            return Room.objects.get(slug=slug)
        except Room.DoesNotExist:
            return None

    @database_sync_to_async
    def get_history(self, room, limit=80):
        messages = room.messages.order_by("-created_at")[:limit]
        return [
            {
                "id": msg.id,
                "username": msg.username,
                "message": msg.content,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in reversed(list(messages))
        ]

    @database_sync_to_async
    def save_message(self, room, username, content):
        msg = Message.objects.create(room=room, username=username, content=content)
        return {
            "id": msg.id,
            "username": msg.username,
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
        }
