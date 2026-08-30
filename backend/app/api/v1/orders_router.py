from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, desc
from backend.app.core.database import get_db
from backend.app.models.order import Order, OrderItem
from backend.app.schemas.order_schema import OrderCreateRequest, OrderResponse, OrderApprovalRequest
from backend.app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/checkout")
async def checkout_order(
    payload: OrderCreateRequest,
    db: Session = Depends(get_db)
):
    return await OrderService.create_order_from_cart(db, payload)

@router.get("", response_model=List[OrderResponse])
def list_orders(
    status: str = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    stmt = select(Order).options(joinedload(Order.items)).order_by(desc(Order.created_at)).limit(limit)
    if status:
        stmt = stmt.where(Order.status == status)
    orders = db.execute(stmt).scalars().unique().all()

    return [OrderService.order_to_response(db, o.id) for o in orders]

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: str,
    db: Session = Depends(get_db)
):
    return OrderService.order_to_response(db, order_id)

@router.post("/approval")
async def approve_or_reject_order(
    payload: OrderApprovalRequest,
    db: Session = Depends(get_db)
):
    return await OrderService.approve_or_reject_hitl_order(
        db=db,
        order_id=payload.order_id,
        decision=payload.decision,
        decision_by=payload.decision_by,
        notes=payload.notes
    )
