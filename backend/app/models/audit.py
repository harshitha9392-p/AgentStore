from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, JSON, Text
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin, get_utc_now

class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    sequence_index = Column(Integer, unique=True, index=True, nullable=False)
    timestamp_iso = Column(String(64), nullable=False)
    session_id = Column(String(128), index=True, nullable=True)
    order_id = Column(String(36), index=True, nullable=True)
    
    actor = Column(String(32), nullable=False) # AGENT, USER, SYSTEM, MERCHANT
    action_type = Column(String(64), nullable=False, index=True)
    
    payload = Column(JSON, default=dict, nullable=False)
    decision_rationale = Column(Text, nullable=True)
    
    previous_hash = Column(String(64), nullable=False)
    block_hash = Column(String(64), unique=True, index=True, nullable=False)
