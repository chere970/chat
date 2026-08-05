"""
REST API views consumed by the React frontend.

Endpoints:
  GET  /api/rooms/            — list rooms (latest 50)
  POST /api/rooms/            — create a room
  GET  /api/rooms/<slug>/     — single room detail
"""
from django.db.models import Count
from django.utils.text import slugify
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Room
from .serializers import RoomSerializer

import re

ROOM_NAME_RE = re.compile(r"^[\w .-]{2,64}$")


@api_view(["GET", "POST"])
def room_list(request):
    if request.method == "GET":
        rooms = Room.objects.annotate(message_count=Count("messages")).order_by(
            "-created_at"
        )[:50]
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data)

    # POST — create room
    name = (request.data.get("name") or "").strip()
    if not ROOM_NAME_RE.match(name):
        return Response(
            {"error": "Room name must be 2–64 chars (letters, numbers, spaces, . - _)."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    slug = slugify(name)[:64]
    if not slug:
        return Response(
            {"error": "Name needs at least one letter or number."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    room, created = Room.objects.get_or_create(slug=slug, defaults={"name": name})
    room = Room.objects.annotate(message_count=Count("messages")).get(pk=room.pk)
    serializer = RoomSerializer(room)
    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


@api_view(["GET"])
def room_detail(request, room_slug):
    try:
        room = Room.objects.annotate(message_count=Count("messages")).get(slug=room_slug)
    except Room.DoesNotExist:
        return Response({"error": "Room not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = RoomSerializer(room)
    return Response(serializer.data)
