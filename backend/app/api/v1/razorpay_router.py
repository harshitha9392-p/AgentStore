from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.core.security import verify_razorpay_webhook_signature
from backend.app.schemas.razorpay_schema import RazorpayPaymentVerifyRequest
from backend.app.services.order_service import OrderService
from backend.app.services.razorpay_service import RazorpayService
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/payments", tags=["Razorpay Payments"])

@router.post("/verify")
def verify_payment(
    payload: RazorpayPaymentVerifyRequest,
    db: Session = Depends(get_db)
):
    return OrderService.verify_and_fulfill_order(
        db=db,
        order_id=payload.order_id,
        razorpay_order_id=payload.razorpay_order_id,
        razorpay_payment_id=payload.razorpay_payment_id,
        razorpay_signature=payload.razorpay_signature
    )

@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None),
    db: Session = Depends(get_db)
):
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")

    if settings.RAZORPAY_WEBHOOK_SECRET and x_razorpay_signature:
        is_valid = verify_razorpay_webhook_signature(
            body_str=body_str,
            received_signature=x_razorpay_signature,
            webhook_secret=settings.RAZORPAY_WEBHOOK_SECRET
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    AuditService.log_financial_decision(
        db=db,
        actor="SYSTEM",
        action_type="RAZORPAY_WEBHOOK_RECEIVED",
        payload={"raw_event": body_str[:500]},
        decision_rationale="Verified Razorpay Webhook Event"
    )

    return {"status": "ok"}
