from sqlalchemy import Column, String, Float, Boolean, JSON
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin

class Merchant(Base, TimestampMixin):
    __tablename__ = "merchants"

    name = Column(String(120), nullable=False)
    slug = Column(String(120), unique=True, index=True, nullable=False)
    email = Column(String(255), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Merchant-specific policy limits
    max_order_value = Column(Float, default=50000.0)
    max_discount_percentage = Column(Float, default=25.0)
    hitl_threshold = Column(Float, default=10000.0)
    daily_transaction_limit = Column(Float, default=100000.0)
    settings = Column(JSON, default=dict)
