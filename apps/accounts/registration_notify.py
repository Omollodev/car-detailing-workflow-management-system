"""
Post-registration notifications: email (required config) + optional SMS.
"""

from __future__ import annotations

import logging
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_customer_registration_email(*, name: str, email: str, username: str) -> None:
    if not email:
        return
    subject = f"Welcome — {settings.BUSINESS_NAME or 'Car Detailing'}"
    body = (
        f"Hi {name},\n\n"
        f"Your customer account is ready.\n"
        f"Username: {username}\n\n"
        f"You can sign in and book services anytime.\n\n"
        f"— {settings.BUSINESS_NAME or 'The team'}"
    )
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or "noreply@localhost"
    try:
        send_mail(
            subject,
            body,
            from_email,
            [email],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Failed to send registration email to %s", email)


def send_customer_verification_email(*, name: str, email: str, verification_url: str) -> None:
    if not email:
        return
    subject = f"Verify your email — {settings.BUSINESS_NAME or 'Car Detailing'}"
    body = (
        f"Hi {name},\n\n"
        "Thanks for registering. Please verify your email before logging in.\n\n"
        f"Verify here: {verification_url}\n\n"
        "If you did not create this account, please ignore this email.\n\n"
        f"— {settings.BUSINESS_NAME or 'The team'}"
    )
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or "noreply@localhost"
    try:
        send_mail(
            subject,
            body,
            from_email,
            [email],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Failed to send verification email to %s", email)


def _send_africastalking_sms(phone_e164: str, message: str) -> bool:
    username = getattr(settings, "AT_USERNAME", "") or ""
    api_key = getattr(settings, "AT_API_KEY", "") or ""
    if not username or not api_key:
        return False

    # Africa's Talking expects comma-separated recipients, often +254...
    data = urllib.parse.urlencode(
        {
            "username": username,
            "to": phone_e164,
            "message": message[:480],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.africastalking.com/version1/messaging",
        data=data,
        headers={
            "apiKey": api_key,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        logger.info("Africa's Talking SMS response: %s", raw[:200])
        return True
    except urllib.error.HTTPError as e:
        logger.warning(
            "Africa's Talking SMS HTTP error: %s %s",
            e.code,
            e.read().decode("utf-8", errors="replace")[:500],
        )
    except Exception:
        logger.exception("Africa's Talking SMS failed")
    return False


def normalize_phone_for_sms_ke(phone: str) -> str | None:
    """Return +254... for Africa's Talking, or None if invalid."""
    digits = "".join(c for c in (phone or "") if c.isdigit())
    if digits.startswith("254") and len(digits) >= 12:
        return "+" + digits[:12]
    if digits.startswith("0") and len(digits) >= 10:
        return "+254" + digits[1:12]
    if len(digits) == 9 and digits.startswith("7"):
        return "+254" + digits
    return None


def send_customer_registration_sms(*, name: str, phone: str) -> None:
    if not getattr(settings, "REGISTRATION_SMS_ENABLED", False):
        return
    to = normalize_phone_for_sms_ke(phone)
    if not to:
        logger.info("Skipping registration SMS: could not parse phone %r", phone)
        return
    msg = (
        f"Hi {name.split()[0] if name else 'there'}, "
        f"your account at {settings.BUSINESS_NAME or 'our car detailing service'} is ready. "
        f"You can log in and book services."
    )
    _send_africastalking_sms(to, msg)


def notify_customer_registered(*, name: str, email: str, phone: str, username: str) -> None:
    send_customer_registration_email(name=name, email=email, username=username)
    send_customer_registration_sms(name=name, phone=phone)
