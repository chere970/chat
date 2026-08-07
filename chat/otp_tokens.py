"""Signed tokens issued after OTP verification for WebSocket room access."""

from django.core.signing import BadSignature, SignatureExpired, TimestampSigner

SIGNER = TimestampSigner(salt="chat-room-otp-access")
TOKEN_MAX_AGE_SECONDS = 8 * 3600  # align with a typical browser session


def issue_room_access_token(room_slug: str, phone_number: str) -> str:
    return SIGNER.sign(f"{room_slug}:{phone_number}")


def verify_room_access_token(token: str, room_slug: str, phone_number: str) -> bool:
    if not token:
        return False
    try:
        payload = SIGNER.unsign(token, max_age=TOKEN_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return False
    parts = payload.split(":", 1)
    if len(parts) != 2:
        return False
    token_slug, token_phone = parts
    return token_slug == room_slug and token_phone == phone_number
