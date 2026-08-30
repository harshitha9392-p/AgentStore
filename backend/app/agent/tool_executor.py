from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.app.schemas.catalog_schema import CatalogSearchFilter
from backend.app.schemas.cart_schema import AddToCartRequest
from backend.app.schemas.order_schema import OrderCreateRequest
from backend.app.services.catalog_service import CatalogService
from backend.app.services.offer_engine import OfferEngine
from backend.app.services.order_service import OrderService
from backend.app.services.audit_service import AuditService

class ToolExecutor:
    @staticmethod
    async def execute_tool(
        db: Session,
        session_id: str,
        tool_name: str,
        tool_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Safely executes canonical commerce tools requested by the AI agent."""
        try:
            if tool_name == "search_catalog":
                sf = CatalogSearchFilter(
                    query=tool_args.get("query"),
                    category=tool_args.get("category"),
                    min_price=tool_args.get("min_price"),
                    max_price=tool_args.get("max_price"),
                    in_stock_only=tool_args.get("in_stock_only", True),
                    limit=tool_args.get("limit", 6)
                )
                products = CatalogService.search_catalog(db, sf)
                return {
                    "success": True,
                    "count": len(products),
                    "products": [p.model_dump() for p in products]
                }

            elif tool_name == "get_product_details":
                pid = tool_args.get("product_id_or_sku")
                product = CatalogService.get_product(db, pid)
                if product:
                    return {"success": True, "product": product.model_dump()}
                return {"success": False, "error": f"Product '{pid}' not found"}

            elif tool_name == "add_to_cart":
                pid = tool_args.get("product_id")
                qty = tool_args.get("quantity", 1)
                meta = {}
                if "bundle_discount_pct" in tool_args:
                    meta["bundle_discount_pct"] = tool_args["bundle_discount_pct"]

                cart_view = OrderService.add_item_to_cart(db, AddToCartRequest(
                    session_id=session_id,
                    product_id=pid,
                    quantity=qty,
                    metadata=meta
                ))

                cart = OrderService.get_or_create_cart(db, session_id)
                bundles = OfferEngine.evaluate_bundles_for_cart(db, cart)
                upsells = OfferEngine.calculate_upsell_tiers(cart)

                return {
                    "success": True,
                    "message": f"Added {qty} item(s) to cart.",
                    "cart": cart_view.model_dump(),
                    "recommended_bundles": [b.model_dump() for b in bundles],
                    "upsell_tiers": [u.model_dump() for u in upsells]
                }

            elif tool_name == "get_cart":
                cart_view = OrderService.cart_to_view(db, session_id)
                return {"success": True, "cart": cart_view.model_dump()}

            elif tool_name == "recommend_bundles_and_upsells":
                cart = OrderService.get_or_create_cart(db, session_id)
                bundles = OfferEngine.evaluate_bundles_for_cart(db, cart)
                upsells = OfferEngine.calculate_upsell_tiers(cart)
                return {
                    "success": True,
                    "bundles": [b.model_dump() for b in bundles],
                    "upsells": [u.model_dump() for u in upsells]
                }

            elif tool_name == "apply_coupon":
                code = tool_args.get("coupon_code", "")
                cart = OrderService.get_or_create_cart(db, session_id)
                result = OfferEngine.apply_coupon_to_cart(db, cart, code)
                cart_view = OrderService.cart_to_view(db, session_id)
                result["cart"] = cart_view.model_dump()
                return result

            elif tool_name == "initiate_checkout":
                req = OrderCreateRequest(
                    session_id=session_id,
                    customer_name=tool_args.get("customer_name", "Shopper"),
                    customer_email=tool_args.get("customer_email", "customer@example.com"),
                    customer_phone=tool_args.get("customer_phone", "+919876543210"),
                    shipping_address={"address": tool_args.get("shipping_address", "Default Address")}
                )
                checkout_res = await OrderService.create_order_from_cart(db, req)
                return {
                    "success": True,
                    "data": checkout_res
                }

            else:
                return {"success": False, "error": f"Unknown tool name: {tool_name}"}

        except Exception as ex:
            return {
                "success": False,
                "error_type": type(ex).__name__,
                "error": str(ex)
            }
