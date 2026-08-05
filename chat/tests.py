from django.test import TestCase
from django.urls import reverse

from channels.testing import WebsocketCommunicator

from chat.models import Message, Room
from chatapp.asgi import application


class RoomModelTests(TestCase):
    def test_slug_auto_generated(self):
        room = Room.objects.create(name="Design Critique")
        self.assertEqual(room.slug, "design-critique")


class HomeViewTests(TestCase):
    def test_home_renders(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Relay")

    def test_create_room_redirects(self):
        response = self.client.post(
            reverse("create_room"),
            {"name": "general", "display_name": "Alex"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Room.objects.filter(slug="general").exists())
        self.assertEqual(self.client.session["display_name"], "Alex")


class ChatConsumerTests(TestCase):
    async def test_chat_roundtrip(self):
        room = await Room.objects.acreate(name="Lobby", slug="lobby")
        communicator = WebsocketCommunicator(application, "/ws/chat/lobby/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        history = await communicator.receive_json_from()
        self.assertEqual(history["type"], "history")

        await communicator.send_json_to({"type": "join", "username": "Sam"})
        presence = await communicator.receive_json_from()
        self.assertEqual(presence["type"], "presence")
        self.assertEqual(presence["event"], "join")

        await communicator.send_json_to(
            {"type": "chat_message", "message": "Hello Relay"}
        )
        payload = await communicator.receive_json_from()
        self.assertEqual(payload["type"], "chat_message")
        self.assertEqual(payload["message"], "Hello Relay")
        self.assertEqual(payload["username"], "Sam")

        self.assertTrue(
            await Message.objects.filter(room=room, content="Hello Relay").aexists()
        )
        await communicator.disconnect()
