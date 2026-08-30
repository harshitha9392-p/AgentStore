from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr

class OrderCreateRequest(BaseModel):
    session_id: str
    customer_name: str
    customer_email: str
    customer_phone: str
    shipping_address: Dict[str, Any]
    idempotency_key: Optional[str] = None

class OrderApprovalRequest(BaseModel):
    order_id: str
    decision: str # APPROVED, REJECTED
    decision_by: str = "Merchant Admin"
    notes: Optional[str] = None

class OrderItemResponse(BaseModel):
    product_id: str
    product_name: str
    sku: str
    unit_price: float
    quantity: int
    discount_amount: float
    total_price: float

class OrderResponse(BaseModel):
    id: str
    order_number: str
    status: str
    currency: str
    subtotal: float
    discount_amount: float
    tax_amount: float
    shipping_fee: float
    total_amount: float
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    items: List[OrderItemResponse] = []
    applied_offers: List[Dict[str, Any]] = []
    created_at: str
