"""
SMS sending utility — pluggable backend.

Supported backends (set via SMS_BACKEND env var):
  "afromessage"  — AfroMessage (afromessage.com) — recommended for Ethiopia
  "twilio"       — Twilio (twilio.com)
  "console"      — prints to console (default / development)

Each backend is auto-detected from environment variables:
  - AfroMessage: AFROMESSAGE_TOKEN (+ optional AFROMESSAGE_IDENTIFIER_ID, AFROMESSAGE_SENDER)
  - Twilio:      TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER

If SMS_BACKEND is not set, the code auto-selects based on which env vars are present.
"""

import logging
import random
import string

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

OTP_TTL_SECONDS = 300


def get_sms_backend():
    """Determine which SMS backend to use."""
    explicit = getattr(settings, "SMS_BACKEND", "").lower()
    if explicit:
        return explicit

    if getattr(settings, "AFROMESSAGE_TOKEN", ""):
        return "afromessage"
    if all([
        getattr(settings, "TWILIO_ACCOUNT_SID", ""),
        getattr(settings, "TWILIO_AUTH_TOKEN", ""),
        getattr(settings, "TWILIO_PHONE_NUMBER", ""),
    ]):
        return "twilio"

    return "console"


def _afromessage_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _afromessage_params(**extra) -> dict:
    """Build common AfroMessage query params (from, sender)."""
    params = dict(extra)
    identifier_id = getattr(settings, "AFROMESSAGE_IDENTIFIER_ID", "")
    sender = getattr(settings, "AFROMESSAGE_SENDER", "")
    if identifier_id:
        params["from"] = identifier_id
    if sender:
        params["sender"] = sender
    return params


# ── AfroMessage ──────────────────────────────────────────────────

def _send_afromessage(to: str, body: str) -> bool:
    """Send SMS via AfroMessage API (https://api.afromessage.com)."""
    token = getattr(settings, "AFROMESSAGE_TOKEN", "")
    if not token:
        logger.error("AFROMESSAGE_TOKEN is not configured.")
        return False

    try:
        params = _afromessage_params(to=to, message=body)
        response = requests.get(
            "https://api.afromessage.com/api/send",
            params=params,
            headers=_afromessage_headers(token),
            timeout=15,
        )

        data = response.json()
        if data.get("acknowledge") == "success":
            logger.info("AfroMessage SMS sent to %s", to)
            return True

        logger.error("AfroMessage error: %s", data)
        return False

    except Exception as e:
        logger.error("AfroMessage SMS failed to %s: %s", to, e)
        return False


def _send_afromessage_otp(
    to: str,
    code_length: int = 6,
    ttl: int = OTP_TTL_SECONDS,
    room_name: str = "",
) -> dict | None:
    """Send OTP via AfroMessage's /api/challenge endpoint.

    Returns the full API response on success, or None on failure.
    AfroMessage generates the code and returns a verificationId for later use.
    """
    token = getattr(settings, "AFROMESSAGE_TOKEN", "")
    if not token:
        logger.error("AFROMESSAGE_TOKEN is not configured.")
        return None

    try:
        params = _afromessage_params(
            to=to,
            len=code_length,
            t=0,
            ttl=ttl,
        )
        if room_name:
            params["pr"] = f'Your Relay code to join "{room_name}" is'

        response = requests.get(
            "https://api.afromessage.com/api/challenge",
            params=params,
            headers=_afromessage_headers(token),
            timeout=15,
        )

        data = response.json()
        if data.get("acknowledge") == "success":
            logger.info("AfroMessage OTP sent to %s", to)
            return data

        logger.error("AfroMessage OTP error: %s", data)
        return None

    except Exception as e:
        logger.error("AfroMessage OTP failed to %s: %s", to, e)
        return None


def _verify_afromessage_otp(
    to: str,
    code: str,
    verification_id: str = "",
) -> bool:
    """Verify an OTP via AfroMessage's /api/verify endpoint."""
    token = getattr(settings, "AFROMESSAGE_TOKEN", "")
    if not token:
        logger.error("AFROMESSAGE_TOKEN is not configured.")
        return False

    try:
        params = {"code": code}
        if verification_id:
            params["vc"] = verification_id
        else:
            params["to"] = to

        response = requests.get(
            "https://api.afromessage.com/api/verify",
            params=params,
            headers=_afromessage_headers(token),
            timeout=15,
        )

        data = response.json()
        if data.get("acknowledge") == "success":
            logger.info("AfroMessage OTP verified for %s", to)
            return True

        logger.warning("AfroMessage OTP verification failed: %s", data)
        return False

    except Exception as e:
        logger.error("AfroMessage OTP verify failed for %s: %s", to, e)
        return False


# ── Twilio ───────────────────────────────────────────────────────

def _send_twilio(to: str, body: str) -> bool:
    """Send SMS via Twilio."""
    account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", "")
    auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", "")
    from_number = getattr(settings, "TWILIO_PHONE_NUMBER", "")

    if not all([account_sid, auth_token, from_number]):
        logger.error("Twilio credentials are not fully configured.")
        return False

    try:
        from twilio.rest import Client

        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=body,
            from_=from_number,
            to=to,
        )
        logger.info("Twilio SMS sent to %s — SID: %s", to, message.sid)
        return True
    except ImportError:
        logger.error("twilio package not installed. Run: pip install twilio")
        return False
    except Exception as e:
        logger.error("Twilio SMS failed to %s: %s", to, e)
        return False


# ── Console (dev fallback) ───────────────────────────────────────

def _send_console(to: str, body: str) -> bool:
    """Log SMS to console for development."""
    logger.info("[DEV SMS] To: %s | Message: %s", to, body)
    print(f"\n{'='*50}")
    print(f"  📱 SMS to {to}")
    print(f"  📝 {body}")
    print(f"{'='*50}\n")
    return True


# ── Public API ───────────────────────────────────────────────────

def send_sms(to: str, body: str) -> bool:
    """Send an SMS message using the configured backend."""
    backend = get_sms_backend()

    if backend == "afromessage":
        return _send_afromessage(to, body)
    if backend == "twilio":
        return _send_twilio(to, body)
    return _send_console(to, body)


def send_otp_sms(to: str, code: str, room_name: str) -> bool:
    """Send a locally-generated OTP code via SMS for room access."""
    body = (
        f"Your Relay verification code is: {code}\n"
        f'Use it to join the room "{room_name}".\n'
        f"This code expires in 5 minutes."
    )
    return send_sms(to, body)


def send_room_otp(to: str, room_name: str) -> dict | None:
    """Send an OTP for room access using the configured backend.

    Returns a dict on success:
      - AfroMessage: {"verification_id": "..."}
      - Twilio/console: {"code": "123456"}
    """
    backend = get_sms_backend()

    if backend == "afromessage":
        data = _send_afromessage_otp(to, room_name=room_name)
        if not data:
            return None
        response = data.get("response") or {}
        verification_id = response.get("verificationId", "")
        if not verification_id:
            logger.error("AfroMessage OTP response missing verificationId: %s", data)
            return None
        return {"verification_id": verification_id}

    code = "".join(random.choices(string.digits, k=6))
    if send_otp_sms(to, code, room_name):
        return {"code": code}
    return None


def verify_room_otp(to: str, code: str, verification_id: str = "") -> bool:
    """Verify an OTP via AfroMessage when a verification_id is present."""
    if get_sms_backend() == "afromessage" and verification_id:
        return _verify_afromessage_otp(to, code, verification_id)
    return False


def is_production_sms():
    """Check if a real SMS backend is configured (not console)."""
    return get_sms_backend() != "console"
