"""
REST API views consumed by the React frontend.

Endpoints:
  GET  /api/rooms/            — list rooms (latest 50)
  POST /api/rooms/            — create a room (optionally with phone_number)
  GET  /api/rooms/<slug>/     — single room detail
  POST /api/otp/send/         — send OTP to a phone number for a room
  POST /api/otp/verify/       — verify OTP code
"""
import logging
import re

from django.db.models import Count
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import PhoneOTP, Room
from .serializers import RoomSerializer, SendOTPSerializer, VerifyOTPSerializer
from .sms import is_production_sms, send_otp_sms

logger = logging.getLogger(__name__)

ROOM_NAME_RE = re.compile(r"^[\w .-]{2,64}$")
PHONE_RE = re.compile(r"^\+?[1-9]\d{6,14}$")


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
    phone_number = (request.data.get("phone_number") or "").strip()

    if not ROOM_NAME_RE.match(name):
        return Response(
            {"error": "Room name must be 2–64 chars (letters, numbers, spaces, . - _)."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if phone_number and not PHONE_RE.match(phone_number):
        return Response(
            {"error": "Invalid phone number. Use format like +1234567890."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    slug = slugify(name)[:64]
    if not slug:
        return Response(
            {"error": "Name needs at least one letter or number."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    defaults = {"name": name}
    if phone_number:
        defaults["phone_number"] = phone_number

    room, created = Room.objects.get_or_create(slug=slug, defaults=defaults)
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


@api_view(["POST"])
def send_otp(request):
    """Generate and 'send' an OTP for a protected room.

    In production, integrate with Twilio/Vonage/etc. to send an SMS.
    For demo purposes, the OTP is returned in the response.
    """
    serializer = SendOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    phone_number = serializer.validated_data["phone_number"]
    room_slug = serializer.validated_data["room_slug"]

    if not PHONE_RE.match(phone_number):
        return Response(
            {"error": "Invalid phone number format."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        room = Room.objects.get(slug=room_slug)
    except Room.DoesNotExist:
        return Response({"error": "Room not found."}, status=status.HTTP_404_NOT_FOUND)

    if not room.is_protected:
        return Response(
            {"error": "This room does not require OTP verification."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if the phone number matches the room's registered number
    if phone_number != room.phone_number:
        return Response(
            {"error": "This phone number is not authorized for this room."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Rate limit: max 3 OTPs per phone per room in the last 10 minutes
    recent_count = PhoneOTP.objects.filter(
        phone_number=phone_number,
        room=room,
        created_at__gte=timezone.now() - timezone.timedelta(minutes=10),
    ).count()
    if recent_count >= 3:
        return Response(
            {"error": "Too many OTP requests. Please wait before trying again."},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    # Invalidate previous unused OTPs
    PhoneOTP.objects.filter(
        phone_number=phone_number, room=room, is_verified=False
    ).update(is_verified=True)

    # Create new OTP
    otp = PhoneOTP(
        phone_number=phone_number,
        room=room,
        expires_at=timezone.now() + timezone.timedelta(minutes=5),
    )
    otp.save()

    # Send the OTP via SMS (Twilio if configured, console fallback otherwise)
    sms_sent = send_otp_sms(phone_number, otp.code, room.name)
    if not sms_sent:
        logger.error("Failed to send OTP SMS to %s for room %s", phone_number, room.slug)
        return Response(
            {"error": "Failed to send SMS. Please try again later."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    response_data = {
        "message": "OTP sent successfully.",
        "expires_in": 300,
    }

    # Only include the OTP code in the response when no real SMS provider is
    # configured (development/demo mode). In production the code is delivered
    # exclusively via SMS.
    if not is_production_sms():
        response_data["otp_code"] = otp.code  # DEV ONLY

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
def verify_otp(request):
    """Verify an OTP code for room access."""
    serializer = VerifyOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    phone_number = serializer.validated_data["phone_number"]
    room_slug = serializer.validated_data["room_slug"]
    code = serializer.validated_data["code"]

    try:
        room = Room.objects.get(slug=room_slug)
    except Room.DoesNotExist:
        return Response({"error": "Room not found."}, status=status.HTTP_404_NOT_FOUND)

    # Find the latest unverified OTP for this phone+room
    otp = (
        PhoneOTP.objects.filter(
            phone_number=phone_number,
            room=room,
            is_verified=False,
        )
        .order_by("-created_at")
        .first()
    )

    if not otp:
        return Response(
            {"error": "No OTP found. Please request a new one."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Track attempts
    otp.attempts += 1
    otp.save(update_fields=["attempts"])

    if otp.is_expired:
        return Response(
            {"error": "OTP has expired. Please request a new one."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if otp.attempts > 5:
        return Response(
            {"error": "Too many failed attempts. Please request a new OTP."},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    if otp.code != code:
        remaining = 5 - otp.attempts
        return Response(
            {"error": f"Invalid OTP code. {remaining} attempts remaining."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Mark as verified
    otp.is_verified = True
    otp.save(update_fields=["is_verified"])

    return Response(
        {
            "message": "OTP verified successfully.",
            "room_slug": room.slug,
            "verified": True,
        },
        status=status.HTTP_200_OK,
    )
