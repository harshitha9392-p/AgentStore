from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.services.failure_simulation import FailureSimulationService
from backend.app.db.seed_data import seed_database

router = APIRouter(prefix="/demo", tags=["Buildathon Demo & Chaos Simulator"])

@router.post("/seed")
def seed_data(db: Session = Depends(get_db)):
    """Populates the database with rich multi-category products, bundles, offers, and policy rules."""
    seed_database(db)
    return {"success": True, "message": "Demo database successfully seeded with canonical catalog & rules."}

@router.post("/scenarios/stock-out")
def trigger_stock_out_scenario(
    session_id: str = "demo_session_stockout",
    db: Session = Depends(get_db)
):
    return FailureSimulationService.simulate_stock_out(db, session_id)

@router.post("/scenarios/prompt-injection")
def trigger_prompt_injection_scenario(
    session_id: str = "demo_session_injection",
    db: Session = Depends(get_db)
):
    return FailureSimulationService.simulate_prompt_injection_discount_exploit(db, session_id)

@router.post("/scenarios/price-hallucination")
def trigger_price_hallucination_scenario(
    session_id: str = "demo_session_hallucination",
    db: Session = Depends(get_db)
):
    return FailureSimulationService.simulate_price_hallucination(db, session_id)

@router.post("/scenarios/payment-tamper")
def trigger_payment_tamper_scenario(
    order_id: str = "demo_order_tamper",
    db: Session = Depends(get_db)
):
    return FailureSimulationService.simulate_tampered_payment_signature(db, order_id)
