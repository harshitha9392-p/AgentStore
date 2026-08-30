from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.app.core.database import get_db
from backend.app.models.offer import Offer, BundleRule
from backend.app.schemas.offer_schema import OfferResponse, BundleRecommendation, UpsellOpportunity
from backend.app.services.order_service import OrderService
from backend.app.services.offer_engine import OfferEngine

router = APIRouter(prefix="/offers", tags=["Offers & Upsell Engine"])

@router.get("/active", response_model=List[OfferResponse])
def list_active_offers(db: Session = Depends(get_db)):
    stmt = select(Offer).where(Offer.is_active == True)
    offers = db.execute(stmt).scalars().all()
    return [
        OfferResponse(
            id=o.id,
            code=o.code,
            title=o.title,
            description=o.description,
            discount_type=o.discount_type,
            discount_value=o.discount_value,
            min_cart_value=o.min_cart_value,
            max_discount_cap=o.max_discount_cap,
            is_active=o.is_active
        )
        for o in offers
    ]

@router.get("/evaluate/{session_id}")
def evaluate_cart_offers(
    session_id: str,
    db: Session = Depends(get_db)
):
    cart = OrderService.get_or_create_cart(db, session_id)
    bundles = OfferEngine.evaluate_bundles_for_cart(db, cart)
    upsells = OfferEngine.calculate_upsell_tiers(cart)
    return {
        "bundles": [b.model_dump() for b in bundles],
        "upsells": [u.model_dump() for u in upsells]
    }
