from sqlalchemy import Column, String, Float, Boolean, ForeignKey, JSON, Text
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin

class Offer(Base, TimestampMixin):
    __tablename__ = "offers"

    code = Column(String(64), unique=True, index=True, nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    discount_type = Column(String(20), default="PERCENTAGE", nullable=False) # PERCENTAGE, FIXED
    discount_value = Column(Float, nullable=False) # e.g. 15.0 for 15% or 500.0 for ₹500
    min_cart_value = Column(Float, default=0.0, nullable=False)
    max_discount_cap = Column(Float, default=2000.0, nullable=False)
    valid_categories = Column(JSON, default=list)
    is_active = Column(Boolean, default=True, nullable=False)

class BundleRule(Base, TimestampMixin):
    __tablename__ = "bundle_rules"

    trigger_product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    recommended_product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    bundle_discount_pct = Column(Float, default=10.0, nullable=False)
    pitch_text = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
