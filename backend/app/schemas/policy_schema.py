from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class PolicyRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    rule_type: str # MAX_ORDER_VALUE, MAX_DISCOUNT_PCT, CATEGORY_RESTRICTION, HITL_THRESHOLD, DAILY_LIMIT
    threshold_value: Optional[float] = None
    category_slug: Optional[str] = None
    action: str = "BLOCK" # BLOCK, ESCALATE, WARN
    is_active: bool = True
    rule_config: Dict[str, Any] = {}

class PolicyRuleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    rule_type: str
    threshold_value: Optional[float] = None
    category_slug: Optional[str] = None
    action: str
    is_active: bool

class PolicyViolationDetail(BaseModel):
    policy_name: str
    rule_type: str
    action: str
    requested_value: Any
    allowed_limit: Any
    message: str

class PolicyCheckResult(BaseModel):
    passed: bool
    requires_hitl: bool = False
    violations: List[PolicyViolationDetail] = []
    warnings: List[str] = []
    authoritative_subtotal: float
    authoritative_discount: float
    authoritative_total: float
