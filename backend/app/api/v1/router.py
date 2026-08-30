from fastapi import APIRouter
from backend.app.api.v1.catalog_router import router as catalog_router
from backend.app.api.v1.cart_router import router as cart_router
from backend.app.api.v1.agent_router import router as agent_router
from backend.app.api.v1.offers_router import router as offers_router
from backend.app.api.v1.orders_router import router as orders_router
from backend.app.api.v1.razorpay_router import router as razorpay_router
from backend.app.api.v1.policy_router import router as policy_router
from backend.app.api.v1.audit_router import router as audit_router
from backend.app.api.v1.demo_router import router as demo_router

api_v1_router = APIRouter()
api_v1_router.include_router(catalog_router)
api_v1_router.include_router(cart_router)
api_v1_router.include_router(agent_router)
api_v1_router.include_router(offers_router)
api_v1_router.include_router(orders_router)
api_v1_router.include_router(razorpay_router)
api_v1_router.include_router(policy_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(demo_router)
