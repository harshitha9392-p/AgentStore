from sqlalchemy import Column, String, Float, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin

class Cart(Base, TimestampMixin):
    __tablename__ = "carts"

    session_id = Column(String(128), unique=True, index=True, nullable=False)
    user_id = Column(String(128), nullable=True, index=True)
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=True)
    status = Column(String(32), default="ACTIVE", nullable=False) # ACTIVE, CHECKED_OUT, ABANDONED
    
    subtotal = Column(Float, default=0.0, nullable=False)
    discount_amount = Column(Float, default=0.0, nullable=False)
    total_amount = Column(Float, default=0.0, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)

    applied_coupon = Column(String(64), nullable=True)
    applied_offers = Column(JSON, default=list) # [{offer_id, code, discount, type, reason}]

    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")

class CartItem(Base, TimestampMixin):
    __tablename__ = "cart_items"

    cart_id = Column(String(36), ForeignKey("carts.id"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    variant_id = Column(String(36), ForeignKey("product_variants.id"), nullable=True)
    
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    item_metadata = Column(JSON, default=dict) # e.g. {"bundle_source": "laptop_sleeve_bundle"}

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")
