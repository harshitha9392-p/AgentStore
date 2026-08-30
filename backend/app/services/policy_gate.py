from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from backend.app.core.config import settings
from backend.app.core.exceptions import (
    PolicyViolationException,
    PriceHallucinationException,
    StockUnavailableException
)
from backend.app.models.cart import Cart, CartItem
from backend.app.models.catalog import Product, Category, Inventory
from backend.app.models.merchant import Merchant
from backend.app.models.policy import PolicyRule, PolicyEvaluationLog
from backend.app.schemas.policy_schema import PolicyCheckResult, PolicyViolationDetail
from backend.app.services.audit_service import AuditService

class PolicyGate:
    @staticmethod
    def evaluate_cart_policies(
        db: Session,
        cart: Cart,
        merchant_id: Optional[str] = None
    ) -> PolicyCheckResult:
        """
        NON-BYPASSABLE SERVER-SIDE POLICY GATE:
        Every transaction MUST pass this gate before order creation or Razorpay payment initiation.
        """
        violations: List[PolicyViolationDetail] = []
        warnings: List[str] = []
        requires_hitl = False

        max_order_val = settings.POLICY_MAX_ORDER_VALUE
        max_discount_pct = settings.POLICY_MAX_DISCOUNT_PERCENTAGE
        hitl_thresh = settings.POLICY_HITL_THRESHOLD

        if merchant_id:
            m_stmt = select(Merchant).where(Merchant.id == merchant_id)
            merchant = db.execute(m_stmt).scalar_one_or_none()
            if merchant:
                max_order_val = merchant.max_order_value or max_order_val
                max_discount_pct = merchant.max_discount_percentage or max_discount_pct
                hitl_thresh = merchant.hitl_threshold or hitl_thresh

        # 1. Gate 1: Price Integrity & Anti-Hallucination Verification
        authoritative_subtotal = 0.0
        for item in cart.items:
            p_stmt = (
                select(Product)
                .options(joinedload(Product.inventory), joinedload(Product.category))
                .where(Product.id == item.product_id)
            )
            db_product = db.execute(p_stmt).scalars().unique().first()

            if not db_product:
                violations.append(PolicyViolationDetail(
                    policy_name="PRODUCT_INTEGRITY",
                    rule_type="CATALOG_VALIDITY",
                    action="BLOCK",
                    requested_value=item.product_id,
                    allowed_limit="Active Product ID",
                    message=f"Product '{item.product_id}' does not exist in authoritative catalog."
                ))
                continue

            # Stock check
            stock = db_product.inventory.stock_quantity if db_product.inventory else 0
            if stock < item.quantity:
                violations.append(PolicyViolationDetail(
                    policy_name="STOCK_AVAILABILITY",
                    rule_type="INVENTORY_INTEGRITY",
                    action="BLOCK",
                    requested_value=item.quantity,
                    allowed_limit=stock,
                    message=f"Insufficient inventory for '{db_product.name}'. Requested: {item.quantity}, Available: {stock}"
                ))

            # Price integrity check (authoritative price lock)
            expected_unit_price = db_product.base_price
            if item.item_metadata and "bundle_discount_pct" in item.item_metadata:
                b_pct = item.item_metadata["bundle_discount_pct"]
                expected_unit_price = round(db_product.base_price * (1.0 - (b_pct / 100.0)), 2)

            if abs(item.unit_price - expected_unit_price) > 0.01:
                violations.append(PolicyViolationDetail(
                    policy_name="PRICE_INTEGRITY",
                    rule_type="PRICE_HALLUCINATION_GUARD",
                    action="BLOCK",
                    requested_value=item.unit_price,
                    allowed_limit=expected_unit_price,
                    message=f"Price discrepancy detected for '{db_product.name}'. Agent claimed ₹{item.unit_price}, authoritative DB price is ₹{expected_unit_price}."
                ))

            # Category restriction check
            if db_product.category and db_product.category.is_restricted:
                violations.append(PolicyViolationDetail(
                    policy_name="CATEGORY_RESTRICTION",
                    rule_type="COMPLIANCE_GATE",
                    action="BLOCK",
                    requested_value=db_product.category.name,
                    allowed_limit="Unrestricted Categories Only",
                    message=f"Product '{db_product.name}' is in restricted category '{db_product.category.name}'."
                ))

            authoritative_subtotal += round(expected_unit_price * item.quantity, 2)

        authoritative_subtotal = round(authoritative_subtotal, 2)

        # 2. Gate 2: Max Discount % Ceiling Enforcement
        claimed_discount = cart.discount_amount or 0.0
        effective_discount_pct = round((claimed_discount / max(authoritative_subtotal, 1.0)) * 100.0, 2)
        
        if effective_discount_pct > max_discount_pct:
            violations.append(PolicyViolationDetail(
                policy_name="MAX_DISCOUNT_PERCENTAGE",
                rule_type="DISCOUNT_CAP_GATE",
                action="BLOCK",
                requested_value=effective_discount_pct,
                allowed_limit=max_discount_pct,
                message=f"Requested discount ({effective_discount_pct}%) exceeds strict merchant ceiling of {max_discount_pct}%."
            ))

        authoritative_discount = min(claimed_discount, round(authoritative_subtotal * (max_discount_pct / 100.0), 2))
        authoritative_total = max(0.0, round(authoritative_subtotal - authoritative_discount, 2))

        # 3. Gate 3: Max Order Value Gate
        if authoritative_total > max_order_val:
            violations.append(PolicyViolationDetail(
                policy_name="MAX_ORDER_VALUE",
                rule_type="TRANSACTION_CAP_GATE",
                action="BLOCK",
                requested_value=authoritative_total,
                allowed_limit=max_order_val,
                message=f"Total order amount ₹{authoritative_total:,.2f} exceeds absolute platform limit of ₹{max_order_val:,.2f}."
            ))

        # 4. Gate 4: Human-in-the-Loop (HITL) Threshold Gate
        if authoritative_total > hitl_thresh:
            requires_hitl = True
            warnings.append(
                f"Order amount (₹{authoritative_total:,.2f}) exceeds auto-checkout limit of ₹{hitl_thresh:,.2f}. Escalated to Merchant Human-in-the-Loop approval queue."
            )

        passed = len(violations) == 0

        # Log policy evaluation result
        log_entry = PolicyEvaluationLog(
            session_id=cart.session_id,
            policy_name="COMBINED_POLICY_GATE_CHECK",
            rule_type="PRE_CHECKOUT_GUARD",
            passed=passed,
            requested_value=authoritative_total,
            limit_value=max_order_val,
            violation_reason="; ".join([v.message for v in violations]) if violations else "Passed all policy gates",
            payload_snapshot={
                "subtotal": authoritative_subtotal,
                "discount": authoritative_discount,
                "total": authoritative_total,
                "requires_hitl": requires_hitl,
                "violation_count": len(violations)
            }
        )
        db.add(log_entry)

        # Record financial audit event
        action_type = "POLICY_CHECK_PASSED" if passed else "POLICY_CHECK_FAILED"
        AuditService.log_financial_decision(
            db=db,
            actor="SYSTEM",
            action_type=action_type,
            payload={
                "session_id": cart.session_id,
                "passed": passed,
                "requires_hitl": requires_hitl,
                "authoritative_total": authoritative_total,
                "violations": [v.model_dump() for v in violations]
            },
            decision_rationale=log_entry.violation_reason,
            session_id=cart.session_id
        )

        return PolicyCheckResult(
            passed=passed,
            requires_hitl=requires_hitl,
            violations=violations,
            warnings=warnings,
            authoritative_subtotal=authoritative_subtotal,
            authoritative_discount=authoritative_discount,
            authoritative_total=authoritative_total
        )
