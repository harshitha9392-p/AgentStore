import pytest
from sqlalchemy import select
from backend.app.models.catalog import Product
from backend.app.services.order_service import OrderService
from backend.app.services.offer_engine import OfferEngine
from backend.app.schemas.cart_schema import AddToCartRequest

def test_bundle_recommendation(db_session):
    session_id = "test_bundle_sess"
    
    prod_stmt = select(Product).where(Product.sku == "APPLE-MBA-M3")
    macbook = db_session.execute(prod_stmt).scalars().first()

    OrderService.add_item_to_cart(db_session, AddToCartRequest(
        session_id=session_id,
        product_id=macbook.id,
        quantity=1
    ))

    cart = OrderService.get_or_create_cart(db_session, session_id)
    bundles = OfferEngine.evaluate_bundles_for_cart(db_session, cart)

    assert len(bundles) >= 1
    rec_skus = [b.recommended_product_sku for b in bundles]
    assert "INCASE-SLV-15" in rec_skus or "LOGI-MX-3S" in rec_skus

def test_apply_valid_and_invalid_coupons(db_session):
    session_id = "test_coupon_sess"

    prod_stmt = select(Product).where(Product.sku == "SONY-WH1000XM5")
    sony = db_session.execute(prod_stmt).scalars().first()

    OrderService.add_item_to_cart(db_session, AddToCartRequest(
        session_id=session_id,
        product_id=sony.id,
        quantity=1
    ))

    cart = OrderService.get_or_create_cart(db_session, session_id)

    # 1. Test valid coupon FESTIVE20 (20% off with max cap 2000)
    res_valid = OfferEngine.apply_coupon_to_cart(db_session, cart, "FESTIVE20")
    assert res_valid["success"] is True
    assert res_valid["discount_amount"] == 2000.0

    # 2. Test invalid coupon
    res_invalid = OfferEngine.apply_coupon_to_cart(db_session, cart, "FAKECOUPON99")
    assert res_invalid["success"] is False
