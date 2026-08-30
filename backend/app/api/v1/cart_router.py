from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.cart_schema import CartView, AddToCartRequest, UpdateCartItemRequest
from backend.app.schemas.offer_schema import ApplyOfferRequest
from backend.app.services.order_service import OrderService
from backend.app.services.offer_engine import OfferEngine

router = APIRouter(prefix="/cart", tags=["Cart"])

@router.get("/{session_id}", response_model=CartView)
def get_cart(
    session_id: str,
    db: Session = Depends(get_db)
):
    return OrderService.cart_to_view(db, session_id)

@router.post("/items", response_model=CartView)
def add_item(
    payload: AddToCartRequest,
    db: Session = Depends(get_db)
):
    return OrderService.add_item_to_cart(db, payload)

@router.put("/items", response_model=CartView)
def update_item(
    payload: UpdateCartItemRequest,
    db: Session = Depends(get_db)
):
    return OrderService.update_cart_item(db, payload.session_id, payload.product_id, payload.quantity)

@router.post("/apply-coupon")
def apply_coupon(
    payload: ApplyOfferRequest,
    db: Session = Depends(get_db)
):
    cart = OrderService.get_or_create_cart(db, payload.session_id)
    res = OfferEngine.apply_coupon_to_cart(db, cart, payload.coupon_code)
    cart_view = OrderService.cart_to_view(db, payload.session_id)
    res["cart"] = cart_view
    return res
