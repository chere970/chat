from rest_framework import serializers

from .models import Message, Room


class RoomSerializer(serializers.ModelSerializer):
    message_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Room
        fields = ["id", "name", "slug", "created_at", "message_count"]
        read_only_fields = ["id", "slug", "created_at", "message_count"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "room", "username", "content", "created_at"]
        read_only_fields = ["id", "created_at"]
