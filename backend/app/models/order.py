from sqlalchemy import Column, String, Float, Integer, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin

class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    order_number = Column(String(64), unique=True, index=True, nullable=False)
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=True, index=True)
    cart_id = Column(String(36), ForeignKey("carts.id"), nullable=True)
    session_id = Column(String(128), index=True, nullable=True)
    
    # Customer Details
    customer_name = Column(String(120), nullable=True)
    customer_email = Column(String(255), nullable=True, index=True)
    customer_phone = Column(String(32), nullable=True)
    shipping_address = Column(JSON, default=dict)
    
    # Financial breakdown
    currency = Column(String(10), default="INR", nullable=False)
    subtotal = Column(Float, default=0.0, nullable=False)
    discount_amount = Column(Float, default=0.0, nullable=False)
    tax_amount = Column(Float, default=0.0, nullable=False)
    shipping_fee = Column(Float, default=0.0, nullable=False)
    total_amount = Column(Float, default=0.0, nullable=False)
    
    # Status: CREATED, REQUIRES_MERCHANT_APPROVAL, APPROVED, REJECTED, PAID, FAILED, CANCELLED
    status = Column(String(40), default="CREATED", nullable=False, index=True)
    hitl_decision_by = Column(String(120), nullable=True)
    hitl_decision_notes = Column(Text, nullable=True)
    
    # Razorpay Payment Details
    razorpay_order_id = Column(String(128), unique=True, index=True, nullable=True)
    razorpay_payment_id = Column(String(128), unique=True, index=True, nullable=True)
    razorpay_signature = Column(String(256), nullable=True)
    idempotency_key = Column(String(128), unique=True, index=True, nullable=True)
    
    policy_check_summary = Column(JSON, default=dict)
    applied_offers = Column(JSON, default=list)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base, TimestampMixin):
    __tablename__ = "order_items"

    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    product_name = Column(String(255), nullable=False)
    sku = Column(String(64), nullable=False)
    unit_price = Column(Float, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    discount_amount = Column(Float, default=0.0)
    total_price = Column(Float, nullable=False)
    item_metadata = Column(JSON, default=dict)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
