import pytest
from backend.app.services.razorpay_service import RazorpayService
from backend.app.core.config import settings

@pytest.mark.asyncio
async def test_razorpay_order_creation():
    rzp_order = await RazorpayService.create_order(
        amount_in_rupees=1499.00,
        currency="INR",
        receipt="rcpt_test_001"
    )
    assert rzp_order["amount"] == 149900 # in paise
    assert rzp_order["currency"] == "INR"
    assert "order_" in rzp_order["id"]

def test_razorpay_signature_verification():
    order_id = "order_test_12345"
    payment_id = "pay_test_67890"
    
    # Generate authentic signature
    valid_sig = RazorpayService.generate_mock_valid_signature(order_id, payment_id)
    assert RazorpayService.verify_payment(order_id, payment_id, valid_sig) is True

    # Bad signature
    assert RazorpayService.verify_payment(order_id, payment_id, "forged_signature_xyz") is False
