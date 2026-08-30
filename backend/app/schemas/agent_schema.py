from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class AgentMessage(BaseModel):
    role: str # "user", "assistant", "system", "tool"
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None

class ActionCard(BaseModel):
    card_type: str # "PRODUCT_LIST", "PRODUCT_DETAIL", "BUNDLE_OFFER", "CART_SUMMARY", "CHECKOUT_PROMPT", "POLICY_ALERT", "APPROVAL_PENDING"
    title: str
    data: Dict[str, Any]

class ChatRequest(BaseModel):
    session_id: str
    message: str
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    action_cards: List[ActionCard] = []
    cart_state: Optional[Dict[str, Any]] = None
    tools_executed: List[Dict[str, Any]] = []

class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
