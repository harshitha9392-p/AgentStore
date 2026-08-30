from typing import Optional, Dict, Any
from pydantic import BaseModel

class RazorpayOrderResponse(BaseModel):
    order_id: str
    razorpay_order_id: str
    amount: int # in paise (e.g. 50000 = ₹500.00)
    currency: str = "INR"
    receipt: str
    status: str
    key_id: str
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None

class RazorpayPaymentVerifyRequest(BaseModel):
    order_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

class RazorpayWebhookPayload(BaseModel):
    event: str
    payload: Dict[str, Any]
