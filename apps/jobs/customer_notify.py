"""
Customer notifications for payment and service completion events.
"""

from __future__ import annotations

import logging
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _normalize_phone_for_sms_ke(phone: str) -> str | None:
    digits = "".join(c for c in (phone or "") if c.isdigit())
    if digits.startswith("254") and len(digits) >= 12:
        return "+" + digits[:12]
    if digits.startswith("0") and len(digits) >= 10:
        return "+254" + digits[1:12]
    if len(digits) == 9 and digits.startswith("7"):
        return "+254" + digits
    return None


def _send_africastalking_sms(phone_e164: str, message: str) -> bool:
    username = getattr(settings, "AT_USERNAME", "") or ""
    api_key = getattr(settings, "AT_API_KEY", "") or ""
    if not username or not api_key:
        return False

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
        logger.info("SMS response: %s", raw[:200])
        return True
    except urllib.error.HTTPError as e:
        logger.warning(
            "SMS HTTP error: %s %s",
            e.code,
            e.read().decode("utf-8", errors="replace")[:500],
        )
    except Exception:
        logger.exception("SMS send failed")
    return False


def notify_customer_payment(job: "Job", amount, channel: str) -> None:
    customer = job.customer
    if getattr(settings, "PAYMENT_EMAIL_NOTIFICATIONS_ENABLED", True) and customer.email:
        subject = f"Payment received — Job #{job.id}"
        body = (
            f"Hi {customer.name},\n\n"
            f"We received your {channel} payment of KES {amount} for Job #{job.id} "
            f"({job.vehicle.plate_number}).\n"
            f"Current balance: KES {job.balance_due}.\n\n"
            f"Thank you,\n{settings.BUSINESS_NAME or 'Car Detailing Team'}"
        )
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or "noreply@localhost"
        try:
            send_mail(subject, body, from_email, [customer.email], fail_silently=False)
        except Exception:
            logger.exception("Failed payment email for job %s", job.id)

    if getattr(settings, "PAYMENT_SMS_NOTIFICATIONS_ENABLED", False):
        to = _normalize_phone_for_sms_ke(customer.phone)
        if to:
            _send_africastalking_sms(
                to,
                (
                    f"{settings.BUSINESS_NAME or 'Car Detailing'}: Payment received for "
                    f"Job #{job.id}, KES {amount}. Balance KES {job.balance_due}."
                ),
            )


def notify_customer_services_completed(job: "Job") -> None:
    customer = job.customer
    if getattr(settings, "SERVICE_EMAIL_NOTIFICATIONS_ENABLED", True) and customer.email:
        subject = f"Services completed — Job #{job.id}"
        body = (
            f"Hi {customer.name},\n\n"
            f"All services for your vehicle {job.vehicle.plate_number} are now complete.\n"
            f"Job #{job.id} is ready for your review/pickup.\n\n"
            f"Thank you,\n{settings.BUSINESS_NAME or 'Car Detailing Team'}"
        )
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or "noreply@localhost"
        try:
            send_mail(subject, body, from_email, [customer.email], fail_silently=False)
        except Exception:
            logger.exception("Failed completion email for job %s", job.id)

    if getattr(settings, "SERVICE_SMS_NOTIFICATIONS_ENABLED", False):
        to = _normalize_phone_for_sms_ke(customer.phone)
        if to:
            _send_africastalking_sms(
                to,
                (
                    f"{settings.BUSINESS_NAME or 'Car Detailing'}: Job #{job.id} for "
                    f"{job.vehicle.plate_number} is complete."
                ),
            )

