from rest_framework import serializers

from .models import Message, Room


class RoomSerializer(serializers.ModelSerializer):
    message_count = serializers.IntegerField(read_only=True)
    is_protected = serializers.BooleanField(read_only=True)

    class Meta:
        model = Room
        fields = ["id", "name", "slug", "phone_number", "is_protected", "created_at", "message_count"]
        read_only_fields = ["id", "slug", "created_at", "message_count", "is_protected"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "room", "username", "content", "created_at"]
        read_only_fields = ["id", "created_at"]


class SendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    room_slug = serializers.SlugField(max_length=64)


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    room_slug = serializers.SlugField(max_length=64)
    code = serializers.CharField(max_length=6, min_length=6)
