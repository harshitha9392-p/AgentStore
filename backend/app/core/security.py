import hmac
import hashlib
import json
from typing import Any, Dict

def compute_hmac_sha256(secret: str, message: str) -> str:
    """Compute HMAC-SHA256 hex digest for Razorpay signatures and webhook verification."""
    return hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

def verify_razorpay_payment_signature(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    secret: str
) -> bool:
    """Verify Razorpay payment signature according to official spec (order_id|payment_id)."""
    expected_payload = f"{razorpay_order_id}|{razorpay_payment_id}"
    generated_sig = compute_hmac_sha256(secret, expected_payload)
    return hmac.compare_digest(generated_sig, razorpay_signature)

def verify_razorpay_webhook_signature(
    body_str: str,
    received_signature: str,
    webhook_secret: str
) -> bool:
    """Verify incoming Razorpay webhook X-Razorpay-Signature header."""
    generated_sig = compute_hmac_sha256(webhook_secret, body_str)
    return hmac.compare_digest(generated_sig, received_signature)

def compute_audit_hash(previous_hash: str, timestamp_iso: str, actor: str, action: str, payload: Dict[str, Any]) -> str:
    """Compute immutable cryptographic block hash for the financial ledger."""
    canonical_payload = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    raw_block = f"{previous_hash}|{timestamp_iso}|{actor}|{action}|{canonical_payload}"
    return hashlib.sha256(raw_block.encode("utf-8")).hexdigest()
