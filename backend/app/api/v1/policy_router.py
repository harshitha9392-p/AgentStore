from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.models.policy import PolicyRule
from backend.app.schemas.policy_schema import PolicyRuleResponse, PolicyCheckResult
from backend.app.services.order_service import OrderService
from backend.app.services.policy_gate import PolicyGate

router = APIRouter(prefix="/policies", tags=["Policy Gates"])

@router.get("/rules", response_model=List[PolicyRuleResponse])
def get_policy_rules(db: Session = Depends(get_db)):
    stmt = select(PolicyRule)
    rules = db.execute(stmt).scalars().all()
    
    if not rules:
        return [
            PolicyRuleResponse(id="p1", name="MAX_ORDER_VALUE_CAP", description="Hard maximum single transaction limit", rule_type="MAX_ORDER_VALUE", threshold_value=settings.POLICY_MAX_ORDER_VALUE, action="BLOCK", is_active=True),
            PolicyRuleResponse(id="p2", name="MAX_DISCOUNT_PERCENT_CAP", description="Maximum allowed discount percentage ceiling", rule_type="MAX_DISCOUNT_PCT", threshold_value=settings.POLICY_MAX_DISCOUNT_PERCENTAGE, action="BLOCK", is_active=True),
            PolicyRuleResponse(id="p3", name="HITL_APPROVAL_THRESHOLD", description="Orders exceeding this value require merchant human review", rule_type="HITL_THRESHOLD", threshold_value=settings.POLICY_HITL_THRESHOLD, action="ESCALATE", is_active=True),
            PolicyRuleResponse(id="p4", name="PRICE_INTEGRITY_LOCK", description="Locks exact database canonical price to prevent agent hallucinations", rule_type="PRICE_INTEGRITY", threshold_value=0.0, action="BLOCK", is_active=True),
            PolicyRuleResponse(id="p5", name="CATEGORY_COMPLIANCE_GATE", description="Blocks age-restricted and hazardous products", rule_type="CATEGORY_RESTRICTION", category_slug="restricted", action="BLOCK", is_active=True)
        ]

    return [
        PolicyRuleResponse(
            id=r.id,
            name=r.name,
            description=r.description,
            rule_type=r.rule_type,
            threshold_value=r.threshold_value,
            category_slug=r.category_slug,
            action=r.action,
            is_active=r.is_active
        )
        for r in rules
    ]

@router.post("/evaluate/{session_id}", response_model=PolicyCheckResult)
def evaluate_cart_policies(
    session_id: str,
    db: Session = Depends(get_db)
):
    cart = OrderService.get_or_create_cart(db, session_id)
    return PolicyGate.evaluate_cart_policies(db, cart)
