import uuid
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, or_
from backend.app.core.config import settings
from backend.app.core.exceptions import (
    PolicyViolationException,
    StockUnavailableException,
    HumanApprovalRequiredException,
    PaymentVerificationException
)
from backend.app.models.cart import Cart, CartItem
from backend.app.models.catalog import Product, Inventory
from backend.app.models.order import Order, OrderItem
from backend.app.schemas.cart_schema import CartView, CartItemView, AddToCartRequest
from backend.app.schemas.order_schema import OrderCreateRequest, OrderResponse, OrderItemResponse
from backend.app.services.policy_gate import PolicyGate
from backend.app.services.razorpay_service import RazorpayService
from backend.app.services.audit_service import AuditService

class OrderService:
    @staticmethod
    def get_or_create_cart(db: Session, session_id: str) -> Cart:
        stmt = (
            select(Cart)
            .options(
                joinedload(Cart.items).joinedload(CartItem.product).joinedload(Product.category)
            )
            .where(Cart.session_id == session_id, Cart.status == "ACTIVE")
        )
        cart = db.execute(stmt).scalars().unique().first()

        if not cart:
            cart = Cart(
                session_id=session_id,
                status="ACTIVE",
                subtotal=0.0,
                discount_amount=0.0,
                total_amount=0.0,
                currency="INR"
            )
            db.add(cart)
            db.commit()
            cart = db.execute(stmt).scalars().unique().first()

        return cart

    @staticmethod
    def _recalculate_cart_totals(cart: Cart):
        subtotal = sum(item.total_price for item in cart.items)
        subtotal = round(subtotal, 2)
        cart.subtotal = subtotal

        discount = 0.0
        if cart.applied_offers:
            for off in cart.applied_offers:
                dtype = off.get("discount_type", "PERCENTAGE")
                dval = float(off.get("discount_value", 0.0))
                if dtype == "PERCENTAGE":
                    discount += round(subtotal * (dval / 100.0), 2)
                else:
                    discount += min(dval, subtotal)

        cart.discount_amount = round(discount, 2)
        cart.total_amount = max(0.0, round(subtotal - discount, 2))

    @staticmethod
    def add_item_to_cart(db: Session, req: AddToCartRequest) -> CartView:
        cart = OrderService.get_or_create_cart(db, req.session_id)

        prod_stmt = (
            select(Product)
            .options(joinedload(Product.inventory), joinedload(Product.category))
            .where(or_(Product.id == req.product_id, Product.sku == req.product_id))
        )
        product = db.execute(prod_stmt).scalars().unique().first()

        if not product or not product.is_active:
            raise StockUnavailableException(
                message=f"Product '{req.product_id}' is not available.",
                product_id=req.product_id,
                requested_qty=req.quantity,
                available_stock=0
            )

        stock_qty = product.inventory.stock_quantity if product.inventory else 0
        if stock_qty < req.quantity:
            raise StockUnavailableException(
                message=f"Only {stock_qty} unit(s) of '{product.name}' available in stock.",
                product_id=product.id,
                requested_qty=req.quantity,
                available_stock=stock_qty
            )

        unit_price = product.base_price
        if "bundle_discount_pct" in req.metadata:
            b_pct = float(req.metadata["bundle_discount_pct"])
            unit_price = round(product.base_price * (1.0 - (b_pct / 100.0)), 2)

        existing_item = next((it for it in cart.items if it.product_id == product.id), None)
        if existing_item:
            existing_item.quantity += req.quantity
            existing_item.unit_price = unit_price
            existing_item.total_price = round(unit_price * existing_item.quantity, 2)
            existing_item.item_metadata = req.metadata
        else:
            new_item = CartItem(
                cart_id=cart.id,
                product_id=product.id,
                variant_id=req.variant_id,
                quantity=req.quantity,
                unit_price=unit_price,
                total_price=round(unit_price * req.quantity, 2),
                item_metadata=req.metadata
            )
            cart.items.append(new_item)

        OrderService._recalculate_cart_totals(cart)
        db.commit()
        return OrderService.cart_to_view(db, cart.session_id)

    @staticmethod
    def update_cart_item(db: Session, session_id: str, product_id: str, quantity: int) -> CartView:
        cart = OrderService.get_or_create_cart(db, session_id)
        item = next((it for it in cart.items if it.product_id == product_id or (it.product and it.product.sku == product_id)), None)

        if not item:
            return OrderService.cart_to_view(db, session_id)

        if quantity <= 0:
            cart.items.remove(item)
            db.delete(item)
        else:
            item.quantity = quantity
            item.total_price = round(item.unit_price * quantity, 2)

        OrderService._recalculate_cart_totals(cart)
        db.commit()
        return OrderService.cart_to_view(db, session_id)

    @staticmethod
    def cart_to_view(db: Session, session_id: str) -> CartView:
        cart = OrderService.get_or_create_cart(db, session_id)
        item_views = []
        for it in cart.items:
            p = it.product
            item_views.append(CartItemView(
                id=it.id,
                product_id=it.product_id,
                product_name=p.name if p else "Product",
                sku=p.sku if p else "",
                unit_price=it.unit_price,
                quantity=it.quantity,
                total_price=it.total_price,
                image_url=p.image_url if p else None,
                category_slug=p.category.slug if (p and p.category) else None,
                item_metadata=it.item_metadata or {}
            ))

        return CartView(
            id=cart.id,
            session_id=cart.session_id,
            status=cart.status,
            items=item_views,
            item_count=sum(it.quantity for it in cart.items),
            subtotal=cart.subtotal,
            discount_amount=cart.discount_amount,
            total_amount=cart.total_amount,
            currency=cart.currency,
            applied_coupon=cart.applied_coupon,
            applied_offers=cart.applied_offers or []
        )

    @staticmethod
    async def create_order_from_cart(db: Session, req: OrderCreateRequest) -> Dict[str, Any]:
        """
        Full checkout pipeline with Non-Bypassable Server Policy Gates and Razorpay order generation.
        """
        cart = OrderService.get_or_create_cart(db, req.session_id)
        if not cart.items:
            raise PolicyViolationException(
                message="Cannot initiate checkout with an empty cart.",
                policy_name="CART_EMPTY_CHECK",
                requested_value=0,
                allowed_limit="> 0 items"
            )

        policy_result = PolicyGate.evaluate_cart_policies(db=db, cart=cart)
        if not policy_result.passed:
            err_msg = "; ".join([v.message for v in policy_result.violations])
            raise PolicyViolationException(
                message=f"Order failed server-side policy gate: {err_msg}",
                policy_name=policy_result.violations[0].policy_name,
                requested_value=policy_result.violations[0].requested_value,
                allowed_limit=policy_result.violations[0].allowed_limit,
                details={"violations": [v.model_dump() for v in policy_result.violations]}
            )

        order_num = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        initial_status = "REQUIRES_MERCHANT_APPROVAL" if policy_result.requires_hitl else "CREATED"

        order = Order(
            order_number=order_num,
            merchant_id=cart.merchant_id,
            cart_id=cart.id,
            session_id=cart.session_id,
            customer_name=req.customer_name,
            customer_email=req.customer_email,
            customer_phone=req.customer_phone,
            shipping_address=req.shipping_address,
            currency=cart.currency,
            subtotal=policy_result.authoritative_subtotal,
            discount_amount=policy_result.authoritative_discount,
            tax_amount=0.0,
            shipping_fee=0.0,
            total_amount=policy_result.authoritative_total,
            status=initial_status,
            idempotency_key=req.idempotency_key or f"idemp_{uuid.uuid4().hex[:12]}",
            policy_check_summary=policy_result.model_dump(),
            applied_offers=cart.applied_offers or []
        )
        db.add(order)
        db.flush()

        for it in cart.items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=it.product_id,
                product_name=it.product.name if it.product else "Item",
                sku=it.product.sku if it.product else "",
                unit_price=it.unit_price,
                quantity=it.quantity,
                discount_amount=0.0,
                total_price=it.total_price,
                item_metadata=it.item_metadata or {}
            )
            db.add(order_item)

        AuditService.log_financial_decision(
            db=db,
            actor="USER",
            action_type="ORDER_INITIATED",
            payload={
                "order_id": order.id,
                "order_number": order.order_number,
                "total_amount": order.total_amount,
                "status": order.status,
                "item_count": len(cart.items)
            },
            decision_rationale=f"Order {order.order_number} initialized with total ₹{order.total_amount}",
            session_id=cart.session_id,
            order_id=order.id
        )

        if policy_result.requires_hitl:
            db.commit()
            return {
                "order": OrderService.order_to_response(db, order.id),
                "requires_hitl": True,
                "message": f"Order value ₹{order.total_amount:,.2f} exceeds instant checkout ceiling. Awaiting Merchant Human Approval.",
                "razorpay_order": None
            }

        rzp_order = await RazorpayService.create_order(
            amount_in_rupees=order.total_amount,
            currency=order.currency,
            receipt=order.order_number,
            notes={"order_id": order.id, "session_id": cart.session_id}
        )

        order.razorpay_order_id = rzp_order["id"]
        db.commit()

        AuditService.log_financial_decision(
            db=db,
            actor="SYSTEM",
            action_type="RAZORPAY_ORDER_CREATED",
            payload={
                "order_id": order.id,
                "razorpay_order_id": rzp_order["id"],
                "amount_paise": rzp_order["amount"],
                "currency": rzp_order["currency"]
            },
            decision_rationale=f"Generated Razorpay Order {rzp_order['id']} for amount ₹{order.total_amount}",
            session_id=cart.session_id,
            order_id=order.id
        )

        return {
            "order": OrderService.order_to_response(db, order.id),
            "requires_hitl": False,
            "message": "Razorpay order created successfully.",
            "razorpay_order": {
                "order_id": order.id,
                "razorpay_order_id": rzp_order["id"],
                "amount": rzp_order["amount"],
                "currency": rzp_order["currency"],
                "receipt": rzp_order["receipt"],
                "status": rzp_order["status"],
                "key_id": settings.RAZORPAY_KEY_ID,
                "customer_name": order.customer_name,
                "customer_email": order.customer_email,
                "customer_phone": order.customer_phone
            }
        }

    @staticmethod
    async def approve_or_reject_hitl_order(
        db: Session,
        order_id: str,
        decision: str,
        decision_by: str = "Merchant Admin",
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        stmt = select(Order).where(Order.id == order_id)
        order = db.execute(stmt).scalar_one_or_none()

        if not order:
            raise PolicyViolationException("Order not found", policy_name="ORDER_LOOKUP", requested_value=order_id, allowed_limit="Valid Order ID")

        decision = decision.upper()
        if decision == "APPROVED":
            order.status = "APPROVED"
            order.hitl_decision_by = decision_by
            order.hitl_decision_notes = notes

            rzp_order = await RazorpayService.create_order(
                amount_in_rupees=order.total_amount,
                currency=order.currency,
                receipt=order.order_number,
                notes={"order_id": order.id, "hitl_approved_by": decision_by}
            )
            order.razorpay_order_id = rzp_order["id"]

            AuditService.log_financial_decision(
                db=db,
                actor="MERCHANT",
                action_type="HITL_APPROVED",
                payload={"order_id": order.id, "decision_by": decision_by, "notes": notes, "razorpay_order_id": rzp_order["id"]},
                decision_rationale=f"Merchant {decision_by} approved high-value order {order.order_number}",
                session_id=order.session_id,
                order_id=order.id
            )
        else:
            order.status = "REJECTED"
            order.hitl_decision_by = decision_by
            order.hitl_decision_notes = notes

            AuditService.log_financial_decision(
                db=db,
                actor="MERCHANT",
                action_type="HITL_REJECTED",
                payload={"order_id": order.id, "decision_by": decision_by, "notes": notes},
                decision_rationale=f"Merchant {decision_by} rejected order {order.order_number}",
                session_id=order.session_id,
                order_id=order.id
            )

        db.commit()
        return {"success": True, "status": order.status, "razorpay_order_id": order.razorpay_order_id}

    @staticmethod
    def verify_and_fulfill_order(
        db: Session,
        order_id: str,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str
    ) -> Dict[str, Any]:
        stmt = select(Order).options(joinedload(Order.items)).where(Order.id == order_id)
        order = db.execute(stmt).scalars().unique().first()

        if not order:
            raise PaymentVerificationException("Order not found.", razorpay_order_id=razorpay_order_id)

        is_valid = RazorpayService.verify_payment(
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature
        )

        if not is_valid:
            AuditService.log_financial_decision(
                db=db,
                actor="SYSTEM",
                action_type="PAYMENT_VERIFICATION_FAILED",
                payload={
                    "order_id": order.id,
                    "razorpay_order_id": razorpay_order_id,
                    "razorpay_payment_id": razorpay_payment_id
                },
                decision_rationale="HMAC-SHA256 signature mismatch on payment confirmation.",
                session_id=order.session_id,
                order_id=order.id
            )
            raise PaymentVerificationException("Invalid Razorpay payment signature.", razorpay_order_id=razorpay_order_id, razorpay_payment_id=razorpay_payment_id)

        order.status = "PAID"
        order.razorpay_payment_id = razorpay_payment_id
        order.razorpay_signature = razorpay_signature

        for it in order.items:
            inv_stmt = select(Inventory).where(Inventory.product_id == it.product_id)
            inv = db.execute(inv_stmt).scalar_one_or_none()
            if inv:
                inv.stock_quantity = max(0, inv.stock_quantity - it.quantity)
                inv.is_available = inv.stock_quantity > 0

        if order.cart_id:
            cart_stmt = select(Cart).where(Cart.id == order.cart_id)
            cart = db.execute(cart_stmt).scalar_one_or_none()
            if cart:
                cart.status = "CHECKED_OUT"

        db.commit()

        AuditService.log_financial_decision(
            db=db,
            actor="SYSTEM",
            action_type="PAYMENT_VERIFIED",
            payload={
                "order_id": order.id,
                "order_number": order.order_number,
                "total_paid": order.total_amount,
                "razorpay_payment_id": razorpay_payment_id,
                "status": "PAID"
            },
            decision_rationale=f"Payment verified via Razorpay HMAC signature. Order {order.order_number} marked PAID.",
            session_id=order.session_id,
            order_id=order.id
        )

        return {
            "success": True,
            "order_number": order.order_number,
            "status": "PAID",
            "message": "Payment verified and order confirmed!"
        }

    @staticmethod
    def order_to_response(db: Session, order_id: str) -> OrderResponse:
        stmt = select(Order).options(joinedload(Order.items)).where(Order.id == order_id)
        order = db.execute(stmt).scalars().unique().first()

        items = [
            OrderItemResponse(
                product_id=it.product_id,
                product_name=it.product_name,
                sku=it.sku,
                unit_price=it.unit_price,
                quantity=it.quantity,
                discount_amount=it.discount_amount,
                total_price=it.total_price
            )
            for it in order.items
        ]

        return OrderResponse(
            id=order.id,
            order_number=order.order_number,
            status=order.status,
            currency=order.currency,
            subtotal=order.subtotal,
            discount_amount=order.discount_amount,
            tax_amount=order.tax_amount,
            shipping_fee=order.shipping_fee,
            total_amount=order.total_amount,
            customer_name=order.customer_name,
            customer_email=order.customer_email,
            customer_phone=order.customer_phone,
            razorpay_order_id=order.razorpay_order_id,
            razorpay_payment_id=order.razorpay_payment_id,
            items=items,
            applied_offers=order.applied_offers or [],
            created_at=order.created_at.isoformat()
        )
