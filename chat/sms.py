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
import urllib.parse

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _get_backend():
    """Determine which SMS backend to use."""
    explicit = getattr(settings, "SMS_BACKEND", "").lower()
    if explicit:
        return explicit

    # Auto-detect from environment
    if getattr(settings, "AFROMESSAGE_TOKEN", ""):
        return "afromessage"
    if all([
        getattr(settings, "TWILIO_ACCOUNT_SID", ""),
        getattr(settings, "TWILIO_AUTH_TOKEN", ""),
        getattr(settings, "TWILIO_PHONE_NUMBER", ""),
    ]):
        return "twilio"

    return "console"


# ── AfroMessage ──────────────────────────────────────────────────

def _send_afromessage(to: str, body: str) -> bool:
    """Send SMS via AfroMessage API (https://api.afromessage.com)."""
    token = getattr(settings, "AFROMESSAGE_TOKEN", "")
    identifier_id = getattr(settings, "AFROMESSAGE_IDENTIFIER_ID", "")
    sender = getattr(settings, "AFROMESSAGE_SENDER", "")

    if not token:
        logger.error("AFROMESSAGE_TOKEN is not configured.")
        return False

    try:
        params = {
            "to": to,
            "message": body,
        }
        if identifier_id:
            params["from"] = identifier_id
        if sender:
            params["sender"] = sender

        response = requests.get(
            "https://api.afromessage.com/api/send",
            params=params,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )

        data = response.json()
        if data.get("acknowledge") == "success":
            logger.info("AfroMessage SMS sent to %s", to)
            return True
        else:
            logger.error("AfroMessage error: %s", data)
            return False

    except Exception as e:
        logger.error("AfroMessage SMS failed to %s: %s", to, e)
        return False


def _send_afromessage_otp(to: str, code_length: int = 6) -> dict | None:
    """Send OTP via AfroMessage's /api/challenge endpoint.

    Returns the response data (including verificationId) on success, or None.
    This endpoint lets AfroMessage generate and manage the OTP code itself.
    """
    token = getattr(settings, "AFROMESSAGE_TOKEN", "")
    identifier_id = getattr(settings, "AFROMESSAGE_IDENTIFIER_ID", "")
    sender = getattr(settings, "AFROMESSAGE_SENDER", "")

    if not token:
        logger.error("AFROMESSAGE_TOKEN is not configured.")
        return None

    try:
        params = {
            "to": to,
            "codeLength": code_length,
            "type": "numeric",
        }
        if identifier_id:
            params["from"] = identifier_id
        if sender:
            params["sender"] = sender

        response = requests.get(
            "https://api.afromessage.com/api/challenge",
            params=params,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )

        data = response.json()
        if data.get("acknowledge") == "success":
            logger.info("AfroMessage OTP sent to %s", to)
            return data
        else:
            logger.error("AfroMessage OTP error: %s", data)
            return None

    except Exception as e:
        logger.error("AfroMessage OTP failed to %s: %s", to, e)
        return None


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
    backend = _get_backend()

    if backend == "afromessage":
        return _send_afromessage(to, body)
    elif backend == "twilio":
        return _send_twilio(to, body)
    else:
        return _send_console(to, body)


def send_otp_sms(to: str, code: str, room_name: str) -> bool:
    """Send an OTP code via SMS for room access."""
    body = (
        f"Your Relay verification code is: {code}\n"
        f"Use it to join the room \"{room_name}\".\n"
        f"This code expires in 5 minutes."
    )
    return send_sms(to, body)


def is_production_sms():
    """Check if a real SMS backend is configured (not console)."""
    return _get_backend() != "console"
