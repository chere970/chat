import re

from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_http_methods

from .models import Room

ROOM_NAME_RE = re.compile(r"^[\w .-]{2,64}$")
USERNAME_RE = re.compile(r"^[\w .-]{2,32}$")


def home(request):
    rooms = Room.objects.annotate(message_count=Count("messages"))[:24]
    display_name = request.session.get("display_name", "")
    return render(
        request,
        "chat/home.html",
        {
            "rooms": rooms,
            "display_name": display_name,
        },
    )


@require_http_methods(["POST"])
def set_display_name(request):
    name = (request.POST.get("display_name") or "").strip()
    next_url = request.POST.get("next") or "/"

    if not USERNAME_RE.match(name):
        messages.error(
            request,
            "Display name must be 2–32 characters (letters, numbers, spaces, . - _).",
        )
        return redirect(next_url)

    request.session["display_name"] = name
    return redirect(next_url)


@require_http_methods(["POST"])
def create_room(request):
    name = (request.POST.get("name") or "").strip()
    display_name = (request.POST.get("display_name") or "").strip()

    if display_name and USERNAME_RE.match(display_name):
        request.session["display_name"] = display_name

    if not ROOM_NAME_RE.match(name):
        messages.error(
            request,
            "Room name must be 2–64 characters (letters, numbers, spaces, . - _).",
        )
        return redirect("home")

    slug = slugify(name)[:64]
    if not slug:
        messages.error(request, "Choose a room name with at least one letter or number.")
        return redirect("home")

    room, _created = Room.objects.get_or_create(slug=slug, defaults={"name": name})
    return redirect("room", room_slug=room.slug)


def room(request, room_slug):
    chat_room = get_object_or_404(Room, slug=room_slug)
    history = list(chat_room.messages.order_by("-created_at")[:80])
    history.reverse()
    display_name = request.session.get("display_name", "")
    return render(
        request,
        "chat/room.html",
        {
            "room": chat_room,
            "messages_history": history,
            "display_name": display_name,
        },
    )
