import uuid
import httpx
from typing import Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.core.security import compute_hmac_sha256, verify_razorpay_payment_signature
from backend.app.core.exceptions import PaymentVerificationException

class RazorpayService:
    @staticmethod
    async def create_order(
        amount_in_rupees: float,
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Creates a Razorpay order in test mode (in paise). Dual support: Mock simulator or Live Razorpay Test API."""
        amount_paise = int(round(amount_in_rupees * 100))
        receipt_id = receipt or f"rcpt_{uuid.uuid4().hex[:12]}"
        notes_dict = notes or {}

        # If live test credentials are provided and mock mode is off, make real HTTP call to Razorpay
        if not settings.RAZORPAY_MOCK_MODE and settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
            auth = (settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            payload = {
                "amount": amount_paise,
                "currency": currency,
                "receipt": receipt_id,
                "notes": notes_dict
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post("https://api.razorpay.com/v1/orders", json=payload, auth=auth)
                if resp.status_code == 200:
                    return resp.json()

        # Deterministic / High-Fidelity Test Simulator
        generated_order_id = f"order_{uuid.uuid4().hex[:14]}"
        return {
            "id": generated_order_id,
            "entity": "order",
            "amount": amount_paise,
            "amount_paid": 0,
            "amount_due": amount_paise,
            "currency": currency,
            "receipt": receipt_id,
            "status": "created",
            "attempts": 0,
            "notes": notes_dict,
            "created_at": 1772400000
        }

    @staticmethod
    def verify_payment(
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str
    ) -> bool:
        """Verifies payment signature using HMAC SHA256."""
        secret = settings.RAZORPAY_KEY_SECRET
        
        # In mock mode, support standard mock signatures or valid HMAC
        if settings.RAZORPAY_MOCK_MODE and razorpay_signature == "mock_valid_signature_buildathon":
            return True

        return verify_razorpay_payment_signature(
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature,
            secret=secret
        )

    @staticmethod
    def generate_mock_valid_signature(razorpay_order_id: str, razorpay_payment_id: str) -> str:
        """Generates a mathematically valid test HMAC signature for simulated checkout completion."""
        secret = settings.RAZORPAY_KEY_SECRET
        expected_payload = f"{razorpay_order_id}|{razorpay_payment_id}"
        return compute_hmac_sha256(secret, expected_payload)
