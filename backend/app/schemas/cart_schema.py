from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class AddToCartRequest(BaseModel):
    session_id: str
    product_id: str
    quantity: int = Field(default=1, ge=1)
    variant_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class UpdateCartItemRequest(BaseModel):
    session_id: str
    product_id: str
    quantity: int = Field(..., ge=0)

class CartItemView(BaseModel):
    id: str
    product_id: str
    product_name: str
    sku: str
    unit_price: float
    quantity: int
    total_price: float
    image_url: Optional[str] = None
    category_slug: Optional[str] = None
    item_metadata: Dict[str, Any] = Field(default_factory=dict)

class CartView(BaseModel):
    id: str
    session_id: str
    status: str
    items: List[CartItemView]
    item_count: int
    subtotal: float
    discount_amount: float
    total_amount: float
    currency: str
    applied_coupon: Optional[str] = None
    applied_offers: List[Dict[str, Any]] = Field(default_factory=list)
