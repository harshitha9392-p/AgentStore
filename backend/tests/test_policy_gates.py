import pytest
from sqlalchemy import select
from backend.app.models.catalog import Product
from backend.app.services.order_service import OrderService
from backend.app.services.policy_gate import PolicyGate
from backend.app.schemas.cart_schema import AddToCartRequest

def test_policy_gate_max_discount_cap(db_session):
    """Verifies that an unauthorized discount > 25% is blocked by PolicyGate."""
    session_id = "test_policy_sess_1"
    
    prod_stmt = select(Product).where(Product.sku == "BOAT-ROCK-450")
    prod = db_session.execute(prod_stmt).scalars().first()

    OrderService.add_item_to_cart(db_session, AddToCartRequest(
        session_id=session_id,
        product_id=prod.id,
        quantity=2
    ))

    cart = OrderService.get_or_create_cart(db_session, session_id)
    cart.discount_amount = round(cart.subtotal * 0.80, 2)
    cart.total_amount = round(cart.subtotal * 0.20, 2)
    db_session.commit()

    policy_result = PolicyGate.evaluate_cart_policies(db_session, cart)
    assert policy_result.passed is False
    assert any(v.policy_name == "MAX_DISCOUNT_PERCENTAGE" for v in policy_result.violations)

def test_policy_gate_hitl_escalation(db_session):
    """Verifies that orders exceeding ₹10,000 trigger HITL approval requirement."""
    session_id = "test_hitl_sess_2"
    
    prod_stmt = select(Product).where(Product.sku == "APPLE-MBA-M3")
    prod = db_session.execute(prod_stmt).scalars().first()

    OrderService.add_item_to_cart(db_session, AddToCartRequest(
        session_id=session_id,
        product_id=prod.id,
        quantity=1
    ))

    cart = OrderService.get_or_create_cart(db_session, session_id)
    policy_result = PolicyGate.evaluate_cart_policies(db_session, cart)

    assert policy_result.requires_hitl is True
    assert len(policy_result.warnings) > 0

def test_policy_gate_category_restriction(db_session):
    """Verifies that restricted category products are blocked at checkout."""
    session_id = "test_restricted_sess_3"

    prod_stmt = select(Product).where(Product.sku == "RESTRICTED-DRONE-X")
    prod = db_session.execute(prod_stmt).scalars().first()

    OrderService.add_item_to_cart(db_session, AddToCartRequest(
        session_id=session_id,
        product_id=prod.id,
        quantity=1
    ))

    cart = OrderService.get_or_create_cart(db_session, session_id)
    policy_result = PolicyGate.evaluate_cart_policies(db_session, cart)

    assert policy_result.passed is False
    assert any(v.policy_name == "CATEGORY_RESTRICTION" for v in policy_result.violations)
