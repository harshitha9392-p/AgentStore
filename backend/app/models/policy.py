from sqlalchemy import Column, String, Float, Boolean, ForeignKey, JSON, Text
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin

class PolicyRule(Base, TimestampMixin):
    __tablename__ = "policy_rules"

    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=True, index=True)
    name = Column(String(120), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    rule_type = Column(String(50), nullable=False) # MAX_ORDER_VALUE, MAX_DISCOUNT_PCT, CATEGORY_RESTRICTION, HITL_THRESHOLD, DAILY_LIMIT
    threshold_value = Column(Float, nullable=True)
    category_slug = Column(String(100), nullable=True)
    action = Column(String(20), default="BLOCK", nullable=False) # BLOCK, ESCALATE, WARN
    is_active = Column(Boolean, default=True, nullable=False)
    rule_config = Column(JSON, default=dict)

class PolicyEvaluationLog(Base, TimestampMixin):
    __tablename__ = "policy_evaluation_logs"

    session_id = Column(String(128), index=True, nullable=True)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=True, index=True)
    policy_name = Column(String(120), nullable=False)
    rule_type = Column(String(50), nullable=False)
    passed = Column(Boolean, nullable=False)
    requested_value = Column(Float, nullable=True)
    limit_value = Column(Float, nullable=True)
    violation_reason = Column(Text, nullable=True)
    payload_snapshot = Column(JSON, default=dict)
