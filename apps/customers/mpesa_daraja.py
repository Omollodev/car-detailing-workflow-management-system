"""
Safaricom Daraja payments helper.

This module now uses the B2B PayBill flow (BusinessPayBill) and keeps the
existing ``stk_push`` function name for compatibility with current views.

Configure via environment variables in settings.
Uses only the Python standard library (urllib); no ``requests`` required.
"""

from __future__ import annotations

import base64
import json
import logging
import ssl
import urllib.error
import urllib.request
from decimal import Decimal
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


def _api_base() -> str:
    env = getattr(settings, "MPESA_ENV", "sandbox") or "sandbox"
    if str(env).lower() == "production":
        return "https://api.safaricom.co.ke"
    return "https://sandbox.safaricom.co.ke"


B2B_PAYMENT_REQUEST_PATH = "/mpesa/b2b/v1/paymentrequest"


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
    Initiate B2B PayBill payment request.
    Keeps legacy function name for compatibility with existing call sites.
    """
    if not getattr(settings, "MPESA_DARAJA_ENABLED", False):
        raise RuntimeError("M-Pesa Daraja is not enabled (set MPESA_DARAJA_ENABLED=true).")

    party_a = str(getattr(settings, "MPESA_SHORTCODE", "") or "").strip()
    party_b = str(getattr(settings, "MPESA_PARTY_B", "") or "").strip()
    initiator = str(getattr(settings, "MPESA_INITIATOR", "") or "safi-carwash").strip()
    security_credential = str(
        getattr(settings, "MPESA_SECURITY_CREDENTIAL", "") or ""
    ).strip()
    command_id = str(
        getattr(settings, "MPESA_B2B_COMMAND_ID", "") or "BusinessPayBill"
    ).strip()
    sender_identifier_type = str(
        getattr(settings, "MPESA_SENDER_IDENTIFIER_TYPE", "") or "4"
    ).strip()
    receiver_identifier_type = str(
        getattr(settings, "MPESA_RECEIVER_IDENTIFIER_TYPE", "") or "4"
    ).strip()
    requester = str(getattr(settings, "MPESA_REQUESTER", "") or phone_msisdn).strip()
    timeout_url = str(
        getattr(settings, "MPESA_QUEUE_TIMEOUT_URL", "") or getattr(settings, "MPESA_CALLBACK_URL", "")
    ).strip()
    result_url = str(
        getattr(settings, "MPESA_RESULT_URL", "") or getattr(settings, "MPESA_CALLBACK_URL", "")
    ).strip()

    if not party_a or not party_b or not security_credential or not timeout_url or not result_url:
        raise RuntimeError(
            "MPESA_SHORTCODE, MPESA_PARTY_B, MPESA_SECURITY_CREDENTIAL, "
            "MPESA_QUEUE_TIMEOUT_URL/MPESA_CALLBACK_URL, and "
            "MPESA_RESULT_URL/MPESA_CALLBACK_URL must be set."
        )

    amt = int(Decimal(amount).quantize(Decimal("1")))
    if amt < 1:
        raise ValueError("Amount must be at least 1 KES.")

    token = get_access_token()
    payload = {
        "Initiator": initiator,
        "SecurityCredential": security_credential,
        "CommandID": command_id,
        "Amount": amt,
        "PartyA": party_a,
        "PartyB": int(party_b) if party_b.isdigit() else party_b,
        "SenderIdentifierType": sender_identifier_type,
        "ReceiverIdentifierType": receiver_identifier_type,
        "RecieverIdentifierType": receiver_identifier_type,
        "AccountReference": (account_reference or "Payment")[:20],
        "Requester": int(requester) if requester.isdigit() else requester,
        "Remarks": (transaction_desc or "Payment")[:100],
        "QueueTimeOutURL": timeout_url,
        "ResultURL": result_url,
    }

    url = f"{_api_base()}{B2B_PAYMENT_REQUEST_PATH}"
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
            data = json.loads(resp.read().decode("utf-8"))
            # Keep existing view/model flow working by mapping common B2B ids.
            conversation_id = (
                (data.get("ConversationID") or "").strip()
                or (data.get("OriginatorConversationID") or "").strip()
            )
            if conversation_id and not data.get("CheckoutRequestID"):
                data["CheckoutRequestID"] = conversation_id
            if not data.get("MerchantRequestID"):
                data["MerchantRequestID"] = (data.get("OriginatorConversationID") or "")[:120]
            if data.get("ResponseCode") is None:
                data["ResponseCode"] = "0"
            return data
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
    # STK callback format
    try:
        cb = data["Body"]["stkCallback"]
    except (KeyError, TypeError):
        cb = None

    if cb:
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

    # B2B result callback format
    try:
        result = data["Result"]
    except (KeyError, TypeError):
        return None

    out = {
        "checkout_request_id": (
            result.get("ConversationID")
            or result.get("OriginatorConversationID")
            or ""
        ),
        "result_code": result.get("ResultCode"),
        "result_desc": result.get("ResultDesc") or "",
        "amount": None,
        "mpesa_receipt": None,
        "phone": None,
    }

    params = (result.get("ResultParameters") or {}).get("ResultParameter") or []
    for param in params:
        key = param.get("Key")
        val = param.get("Value")
        if key in ("Amount", "TransactionAmount"):
            out["amount"] = val
        elif key in ("TransactionReceipt", "MpesaReceiptNumber"):
            out["mpesa_receipt"] = str(val) if val is not None else None
        elif key in ("ReceiverPartyPublicName", "PhoneNumber"):
            out["phone"] = str(val) if val is not None else None
    return out
