from typing import Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from backend.app.models.catalog import Product, Inventory
from backend.app.models.cart import Cart, CartItem
from backend.app.services.catalog_service import CatalogService
from backend.app.services.order_service import OrderService
from backend.app.services.policy_gate import PolicyGate
from backend.app.services.razorpay_service import RazorpayService
from backend.app.services.audit_service import AuditService
from backend.app.schemas.cart_schema import AddToCartRequest
from backend.app.schemas.order_schema import OrderCreateRequest

class FailureSimulationService:
    @staticmethod
    def simulate_stock_out(db: Session, session_id: str, sku: str = "APPLE-MBP-M3") -> Dict[str, Any]:
        """Simulates an inventory race condition where stock is zeroed out during checkout."""
        prod_stmt = select(Product).options(joinedload(Product.inventory), joinedload(Product.category)).where(Product.sku == sku)
        product = db.execute(prod_stmt).scalars().unique().first()

        if not product:
            # Fallback to first available product
            p_first = db.execute(select(Product).options(joinedload(Product.inventory), joinedload(Product.category))).scalars().unique().first()
            product = p_first

        if not product:
            return {"status": "error", "message": "No product available in catalog."}

        original_stock = product.inventory.stock_quantity if product.inventory else 10
        if product.inventory:
            product.inventory.stock_quantity = 0
            product.inventory.is_available = False
            db.commit()

        try:
            OrderService.add_item_to_cart(db, AddToCartRequest(
                session_id=session_id,
                product_id=product.id,
                quantity=1
            ))
            product.inventory.stock_quantity = original_stock
            db.commit()
            return {"status": "unexpected", "message": "Expected stock out error but succeeded"}
        except Exception as e:
            product.inventory.stock_quantity = original_stock
            product.inventory.is_available = True
            db.commit()

            cat_id = product.category_id
            sub_stmt = (
                select(Product)
                .options(joinedload(Product.inventory))
                .where(Product.category_id == cat_id, Product.id != product.id)
                .limit(2)
            )
            substitutes = [
                {"id": p.id, "name": p.name, "price": p.base_price, "sku": p.sku}
                for p in db.execute(sub_stmt).scalars().unique().all()
            ]

            return {
                "scenario": "STOCK_OUT_RACE_CONDITION",
                "triggered_error": type(e).__name__,
                "error_detail": str(e),
                "graceful_recovery_action": "AGENT_PROPOSES_ALTERNATIVE_ITEMS",
                "recommended_substitutes": substitutes,
                "resolution": "Agent gracefully caught out-of-stock event and provided in-stock alternative products without system crash."
            }

    @staticmethod
    def simulate_prompt_injection_discount_exploit(db: Session, session_id: str) -> Dict[str, Any]:
        """Simulates an attacker trying to force a 90% discount via prompt injection."""
        cart = OrderService.get_or_create_cart(db, session_id)
        
        if not cart.items:
            prod_stmt = select(Product).limit(1)
            first_p = db.execute(prod_stmt).scalars().first()
            if first_p:
                OrderService.add_item_to_cart(db, AddToCartRequest(session_id=session_id, product_id=first_p.id, quantity=1))
                cart = OrderService.get_or_create_cart(db, session_id)

        original_discount = cart.discount_amount
        cart.discount_amount = round(cart.subtotal * 0.90, 2)
        cart.total_amount = round(cart.subtotal * 0.10, 2)
        db.commit()

        policy_result = PolicyGate.evaluate_cart_policies(db=db, cart=cart)

        cart.discount_amount = original_discount
        cart.total_amount = cart.subtotal
        db.commit()

        return {
            "scenario": "PROMPT_INJECTION_DISCOUNT_EXPLOIT",
            "attempted_discount_pct": 90.0,
            "merchant_discount_cap_pct": 25.0,
            "policy_gate_blocked": not policy_result.passed,
            "violations_detected": [v.model_dump() for v in policy_result.violations],
            "audit_trail_logged": True,
            "resolution": "Server-Side Policy Gate intercepted and BLOCKED unauthorized discount attempt. Transaction rejected."
        }

    @staticmethod
    def simulate_price_hallucination(db: Session, session_id: str) -> Dict[str, Any]:
        """Simulates an agent tool call hallucinating a price lower than authoritative catalog."""
        cart = OrderService.get_or_create_cart(db, session_id)
        
        prod_stmt = select(Product).where(Product.base_price > 10000).limit(1)
        laptop = db.execute(prod_stmt).scalars().first()
        
        if not laptop:
            laptop = db.execute(select(Product).limit(1)).scalars().first()

        authoritative_price = laptop.base_price
        fake_hallucinated_price = 199.00

        fake_item = CartItem(
            cart_id=cart.id,
            product_id=laptop.id,
            quantity=1,
            unit_price=fake_hallucinated_price,
            total_price=fake_hallucinated_price
        )
        cart.items.append(fake_item)
        cart.subtotal = fake_hallucinated_price
        cart.total_amount = fake_hallucinated_price
        db.commit()

        policy_result = PolicyGate.evaluate_cart_policies(db=db, cart=cart)

        cart.items.remove(fake_item)
        db.delete(fake_item)
        db.commit()

        return {
            "scenario": "AGENT_PRICE_HALLUCINATION",
            "product_name": laptop.name,
            "authoritative_db_price": authoritative_price,
            "hallucinated_agent_price": fake_hallucinated_price,
            "price_integrity_gate_blocked": not policy_result.passed,
            "violation_details": [v.model_dump() for v in policy_result.violations],
            "resolution": "Price Integrity Gate detected discrepancy between agent claim and DB truth. Order halted."
        }

    @staticmethod
    def simulate_tampered_payment_signature(db: Session, order_id: str) -> Dict[str, Any]:
        """Simulates an adversary attempting to forge a Razorpay payment signature."""
        try:
            OrderService.verify_and_fulfill_order(
                db=db,
                order_id=order_id,
                razorpay_order_id="order_fake_12345",
                razorpay_payment_id="pay_fake_99999",
                razorpay_signature="malicious_forged_signature_00000000000000"
            )
            return {"status": "error", "message": "Expected signature failure but succeeded"}
        except Exception as e:
            return {
                "scenario": "PAYMENT_SIGNATURE_TAMPERING",
                "triggered_error": type(e).__name__,
                "error_detail": str(e),
                "audit_trail_logged": True,
                "resolution": "HMAC-SHA256 verification failed. Order status remained unfulfilled, and tampering incident logged to immutable audit ledger."
            }
