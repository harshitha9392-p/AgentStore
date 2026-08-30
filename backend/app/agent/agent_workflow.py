import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.schemas.agent_schema import ChatRequest, ChatResponse, ActionCard
from backend.app.agent.llm_adapter import get_llm_adapter
from backend.app.agent.tools import AGENT_TOOLS_DEFINITIONS
from backend.app.agent.tool_executor import ToolExecutor
from backend.app.services.order_service import OrderService
from backend.app.core.redis_client import redis_manager

class AgentWorkflow:
    @staticmethod
    async def process_chat_turn(db: Session, chat_req: ChatRequest) -> ChatResponse:
        session_id = chat_req.session_id
        user_message = chat_req.message

        history_key = f"chat_history:{session_id}"
        history = await redis_manager.get_json(history_key) or []
        history.append({"role": "user", "content": user_message})

        adapter = get_llm_adapter()
        llm_output = await adapter.generate_response_with_tools(
            messages=history,
            tools=AGENT_TOOLS_DEFINITIONS
        )

        reply_text = llm_output.get("content", "")
        tool_calls = llm_output.get("tool_calls", [])
        
        action_cards: List[ActionCard] = []
        executed_tools_summary: List[Dict[str, Any]] = []

        for tc in tool_calls:
            t_name = tc.get("name")
            t_args = tc.get("arguments", {})

            tool_result = await ToolExecutor.execute_tool(
                db=db,
                session_id=session_id,
                tool_name=t_name,
                tool_args=t_args
            )

            executed_tools_summary.append({
                "tool": t_name,
                "args": t_args,
                "result_status": "success" if tool_result.get("success") else "failed"
            })

            if t_name == "search_catalog" and tool_result.get("success"):
                prods = tool_result.get("products", [])
                if prods:
                    action_cards.append(ActionCard(
                        card_type="PRODUCT_LIST",
                        title=f"Matching Products ({len(prods)})",
                        data={"products": prods}
                    ))

            elif t_name == "add_to_cart" and tool_result.get("success"):
                cart_data = tool_result.get("cart")
                action_cards.append(ActionCard(
                    card_type="CART_SUMMARY",
                    title="Cart Updated",
                    data=cart_data
                ))

                bundles = tool_result.get("recommended_bundles", [])
                if bundles:
                    action_cards.append(ActionCard(
                        card_type="BUNDLE_OFFER",
                        title="Special Bundle Discount Offer!",
                        data={"bundles": bundles}
                    ))

                upsells = tool_result.get("upsell_tiers", [])
                if upsells:
                    action_cards.append(ActionCard(
                        card_type="SPEND_TIER_ALERT",
                        title="AOV Reward Opportunity",
                        data={"tiers": upsells}
                    ))

            elif t_name == "get_cart" and tool_result.get("success"):
                action_cards.append(ActionCard(
                    card_type="CART_SUMMARY",
                    title="Your Shopping Cart",
                    data=tool_result.get("cart")
                ))

            elif t_name == "recommend_bundles_and_upsells" and tool_result.get("success"):
                bundles = tool_result.get("bundles", [])
                if bundles:
                    action_cards.append(ActionCard(
                        card_type="BUNDLE_OFFER",
                        title="Recommended Smart Bundles",
                        data={"bundles": bundles}
                    ))

            elif t_name == "apply_coupon":
                if tool_result.get("success"):
                    action_cards.append(ActionCard(
                        card_type="CART_SUMMARY",
                        title=f"Promo Applied: {tool_result.get('message')}",
                        data=tool_result.get("cart")
                    ))
                else:
                    action_cards.append(ActionCard(
                        card_type="POLICY_ALERT",
                        title="Coupon Notice",
                        data={"message": tool_result.get("message")}
                    ))

            elif t_name == "initiate_checkout":
                if tool_result.get("success"):
                    c_data = tool_result.get("data", {})
                    if c_data.get("requires_hitl"):
                        action_cards.append(ActionCard(
                            card_type="APPROVAL_PENDING",
                            title="High-Value Order Pending Merchant Approval",
                            data={
                                "order": c_data.get("order"),
                                "message": c_data.get("message")
                            }
                        ))
                    else:
                        action_cards.append(ActionCard(
                            card_type="CHECKOUT_PROMPT",
                            title="Ready for Razorpay Checkout",
                            data=c_data.get("razorpay_order")
                        ))
                else:
                    action_cards.append(ActionCard(
                        card_type="POLICY_ALERT",
                        title="Checkout Policy Warning",
                        data={"error": tool_result.get("error")}
                    ))

        cart_view = OrderService.cart_to_view(db, session_id)

        history.append({"role": "assistant", "content": reply_text})
        if len(history) > 20:
            history = history[-20:]
        await redis_manager.set_json(history_key, history, ex=86400)

        return ChatResponse(
            session_id=session_id,
            reply=reply_text,
            action_cards=action_cards,
            cart_state=cart_view.model_dump(),
            tools_executed=executed_tools_summary
        )
