from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class OfferResponse(BaseModel):
    id: str
    code: str
    title: str
    description: Optional[str] = None
    discount_type: str
    discount_value: float
    min_cart_value: float
    max_discount_cap: float
    is_active: bool

class BundleRecommendation(BaseModel):
    trigger_product_name: str
    recommended_product_id: str
    recommended_product_name: str
    recommended_product_sku: str
    recommended_product_price: float
    bundle_discount_pct: float
    discounted_price: float
    pitch_text: str
    savings_amount: float

class ApplyOfferRequest(BaseModel):
    session_id: str
    coupon_code: str

class UpsellOpportunity(BaseModel):
    opportunity_type: str # BUNDLE, SPEND_TIER, ACCESSORY
    title: str
    description: str
    potential_savings: float
    target_products: List[Dict[str, Any]] = []
    action_payload: Dict[str, Any] = {}
