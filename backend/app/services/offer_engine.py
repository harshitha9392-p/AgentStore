from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, or_
from backend.app.models.offer import Offer, BundleRule
from backend.app.models.catalog import Product
from backend.app.models.cart import Cart, CartItem
from backend.app.schemas.offer_schema import BundleRecommendation, OfferResponse, UpsellOpportunity
from backend.app.services.audit_service import AuditService

class OfferEngine:
    @staticmethod
    def evaluate_bundles_for_cart(db: Session, cart: Cart) -> List[BundleRecommendation]:
        """Finds active bundle opportunities based on items currently in the user's cart."""
        if not cart.items:
            return []

        cart_product_ids = [item.product_id for item in cart.items]
        stmt = select(BundleRule).where(
            BundleRule.trigger_product_id.in_(cart_product_ids),
            BundleRule.is_active == True
        )
        rules = db.execute(stmt).scalars().all()

        recommendations = []
        for rule in rules:
            if rule.recommended_product_id in cart_product_ids:
                continue

            trigger_prod = next((it.product for it in cart.items if it.product_id == rule.trigger_product_id), None)
            
            rec_stmt = select(Product).options(joinedload(Product.inventory)).where(Product.id == rule.recommended_product_id)
            rec_prod = db.execute(rec_stmt).scalars().unique().first()

            if not rec_prod or not rec_prod.is_active:
                continue

            if rec_prod.inventory and rec_prod.inventory.stock_quantity <= 0:
                continue

            discount_pct = rule.bundle_discount_pct
            savings = round(rec_prod.base_price * (discount_pct / 100.0), 2)
            discounted_price = round(rec_prod.base_price - savings, 2)

            recommendations.append(BundleRecommendation(
                trigger_product_name=trigger_prod.name if trigger_prod else "Your item",
                recommended_product_id=rec_prod.id,
                recommended_product_name=rec_prod.name,
                recommended_product_sku=rec_prod.sku,
                recommended_product_price=rec_prod.base_price,
                bundle_discount_pct=discount_pct,
                discounted_price=discounted_price,
                pitch_text=rule.pitch_text,
                savings_amount=savings
            ))

        return recommendations

    @staticmethod
    def calculate_upsell_tiers(cart: Cart) -> List[UpsellOpportunity]:
        """Generates dynamic threshold upgrade incentives to boost Average Order Value (AOV)."""
        subtotal = cart.subtotal
        tiers = []

        if subtotal < 2000:
            deficit = round(2000 - subtotal, 2)
            tiers.append(UpsellOpportunity(
                opportunity_type="SPEND_TIER",
                title="Unlock 10% Off (Code: SAVE10)",
                description=f"Add items worth ₹{deficit:,.2f} more to unlock 10% instant discount on your entire cart!",
                potential_savings=round((subtotal + deficit) * 0.10, 2),
                action_payload={"coupon_code": "SAVE10", "threshold": 2000}
            ))
        elif subtotal < 5000:
            deficit = round(5000 - subtotal, 2)
            tiers.append(UpsellOpportunity(
                opportunity_type="SPEND_TIER",
                title="Unlock 20% Mega VIP Discount (Code: FESTIVE20)",
                description=f"Add items worth ₹{deficit:,.2f} more to unlock 20% off (up to ₹1,500) + Free Priority Delivery!",
                potential_savings=min(round((subtotal + deficit) * 0.20, 2), 1500.0),
                action_payload={"coupon_code": "FESTIVE20", "threshold": 5000}
            ))

        return tiers

    @staticmethod
    def apply_coupon_to_cart(db: Session, cart: Cart, coupon_code: str) -> Dict[str, Any]:
        """Validates and applies an offer to the cart with strict server-side bounds."""
        coupon_code = coupon_code.strip().upper()
        stmt = select(Offer).where(Offer.code == coupon_code, Offer.is_active == True)
        offer = db.execute(stmt).scalar_one_or_none()

        if not offer:
            return {"success": False, "message": f"Coupon code '{coupon_code}' is invalid or expired."}

        if cart.subtotal < offer.min_cart_value:
            shortfall = offer.min_cart_value - cart.subtotal
            return {
                "success": False,
                "message": f"Coupon '{coupon_code}' requires a minimum order value of ₹{offer.min_cart_value:,.2f}. Add ₹{shortfall:,.2f} more to activate!"
            }

        # Calculate discount
        if offer.discount_type == "PERCENTAGE":
            calc_discount = round(cart.subtotal * (offer.discount_value / 100.0), 2)
            discount = min(calc_discount, offer.max_discount_cap)
        else: # FIXED
            discount = min(offer.discount_value, cart.subtotal)

        cart.applied_coupon = offer.code
        cart.discount_amount = discount
        cart.total_amount = max(0.0, round(cart.subtotal - discount, 2))
        cart.applied_offers = [{
            "offer_id": offer.id,
            "code": offer.code,
            "title": offer.title,
            "discount_amount": discount,
            "discount_type": offer.discount_type,
            "discount_value": offer.discount_value
        }]

        db.commit()
        db.refresh(cart)

        # Record financial offer evaluation in audit trail
        AuditService.log_financial_decision(
            db=db,
            actor="SYSTEM",
            action_type="DISCOUNT_APPLIED",
            payload={
                "coupon_code": offer.code,
                "subtotal": cart.subtotal,
                "discount_amount": discount,
                "new_total": cart.total_amount
            },
            decision_rationale=f"Valid coupon '{offer.code}' applied satisfying min cart threshold ₹{offer.min_cart_value}",
            session_id=cart.session_id
        )

        return {
            "success": True,
            "message": f"Coupon '{offer.code}' applied successfully! You saved ₹{discount:,.2f}.",
            "discount_amount": discount,
            "new_total": cart.total_amount
        }
