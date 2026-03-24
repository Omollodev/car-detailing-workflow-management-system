"""
Safaricom Daraja — Lipa na M-Pesa Online (M-Pesa Express / STK Push).

Merchant-initiated C2B: customer receives an authorization prompt on their phone.

Endpoints:
  Sandbox:    https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest
  Production: https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest

Payload shape matches Daraja samples (string fields for Amount, shortcode, phones).

Configure via environment variables (see MPESA_AND_EMAIL_SETUP.md).
Uses only the Python standard library (urllib); no ``requests`` required.
"""

from __future__ import annotations

import base64
import json
import logging
import ssl
import urllib.error
import urllib.request
from datetime import datetime
from decimal import Decimal
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


def _api_base() -> str:
    env = getattr(settings, "MPESA_ENV", "sandbox") or "sandbox"
    if str(env).lower() == "production":
        return "https://api.safaricom.co.ke"
    return "https://sandbox.safaricom.co.ke"


STK_PROCESS_REQUEST_PATH = "/mpesa/stkpush/v1/processrequest"


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")


def _stk_password(shortcode: str, passkey: str, ts: str) -> str:
    raw = f"{shortcode}{passkey}{ts}"
    return base64.b64encode(raw.encode("utf-8")).decode("ascii")


def get_access_token() -> str:
    key = getattr(settings, "MPESA_CONSUMER_KEY", "") or ""
    secret = getattr(settings, "MPESA_CONSUMER_SECRET", "") or ""
    if not key or not secret:
        raise RuntimeError("MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET must be set.")

    auth = base64.b64encode(f"{key}:{secret}".encode("utf-8")).decode("ascii")
    url = f"{_api_base()}/oauth/v1/generate?grant_type=client_credentials"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Basic {auth}"},
        method="GET",
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"Daraja OAuth failed: {data}")
    return token


def normalize_kenya_msisdn(phone: str) -> str:
    """Return 12-digit MSISDN without + (e.g. 254712345678)."""
    digits = "".join(c for c in (phone or "") if c.isdigit())
    if digits.startswith("254") and len(digits) >= 12:
        return digits[:12]
    if digits.startswith("0") and len(digits) >= 10:
        return "254" + digits[1:12]
    if digits.startswith("7") and len(digits) == 9:
        return "254" + digits
    if len(digits) >= 9:
        return "254" + digits[-9:]
    raise ValueError("Enter a valid Kenyan mobile number (e.g. 07XX XXX XXX).")


def stk_push(
    *,
    phone_msisdn: str,
    amount: Decimal,
    account_reference: str,
    transaction_desc: str,
) -> dict[str, Any]:
    """
    Initiate STK Push. Returns Daraja JSON (includes CheckoutRequestID on success).
    """
    if not getattr(settings, "MPESA_DARAJA_ENABLED", False):
        raise RuntimeError("M-Pesa Daraja is not enabled (set MPESA_DARAJA_ENABLED=true).")

    shortcode = str(getattr(settings, "MPESA_SHORTCODE", "") or "").strip()
    passkey = getattr(settings, "MPESA_PASSKEY", "") or ""
    callback = (getattr(settings, "MPESA_CALLBACK_URL", "") or "").strip()
    tx_type = (
        getattr(settings, "MPESA_TRANSACTION_TYPE", None) or "CustomerPayBillOnline"
    ).strip()

    if not shortcode or not passkey or not callback:
        raise RuntimeError(
            "MPESA_SHORTCODE, MPESA_PASSKEY, and MPESA_CALLBACK_URL must be set."
        )

    amt = int(Decimal(amount).quantize(Decimal("1")))
    if amt < 1:
        raise ValueError("Amount must be at least 1 KES.")

    ts = _timestamp()
    token = get_access_token()
    party_b = str(getattr(settings, "MPESA_PARTY_B", "") or shortcode).strip()

    # Daraja accepts the same shape as their Python sample: mostly string values.
    payload = {
        "BusinessShortCode": shortcode,
        "Password": _stk_password(shortcode, passkey, ts),
        "Timestamp": ts,
        "TransactionType": tx_type,
        "Amount": str(amt),
        "PartyA": phone_msisdn,
        "PartyB": party_b,
        "PhoneNumber": phone_msisdn,
        "CallBackURL": callback,
        "AccountReference": (account_reference or "Payment")[:12],
        "TransactionDesc": (transaction_desc or "Payment")[:13],
    }

    url = f"{_api_base()}{STK_PROCESS_REQUEST_PATH}"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=45, context=ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        try:
            err_json = json.loads(err_body)
        except json.JSONDecodeError:
            raise RuntimeError(
                f"M-Pesa STK HTTP {e.code}: {err_body[:500] or e.reason}"
            ) from e
        raise RuntimeError(
            f"M-Pesa STK error: {err_json}"
        ) from e


def parse_stk_callback_body(raw: bytes) -> dict[str, Any]:
    """Parse JSON POST body from Daraja STK callback."""
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        logger.warning("Invalid M-Pesa callback JSON")
        return {}


def extract_stk_result(data: dict[str, Any]) -> dict[str, Any] | None:
    """
    Return dict with checkout_request_id, result_code, amount, receipt, phone or None.
    """
    try:
        cb = data["Body"]["stkCallback"]
    except (KeyError, TypeError):
        return None

    checkout_id = cb.get("CheckoutRequestID") or ""
    result_code = cb.get("ResultCode")
    result_desc = cb.get("ResultDesc") or ""

    out: dict[str, Any] = {
        "checkout_request_id": checkout_id,
        "result_code": result_code,
        "result_desc": result_desc,
        "amount": None,
        "mpesa_receipt": None,
        "phone": None,
    }

    meta = cb.get("CallbackMetadata") or {}
    items = meta.get("Item") or []
    for item in items:
        name = item.get("Name")
        val = item.get("Value")
        if name == "Amount":
            out["amount"] = val
        elif name == "MpesaReceiptNumber":
            out["mpesa_receipt"] = str(val) if val is not None else None
        elif name == "PhoneNumber":
            out["phone"] = str(val) if val is not None else None
    return out
