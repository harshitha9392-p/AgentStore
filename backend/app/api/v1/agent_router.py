from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.redis_client import redis_manager
from backend.app.schemas.agent_schema import ChatRequest, ChatResponse
from backend.app.agent.agent_workflow import AgentWorkflow
from backend.app.agent.tools import AGENT_TOOLS_DEFINITIONS

router = APIRouter(prefix="/agent", tags=["AI Commerce Agent"])

@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    payload: ChatRequest,
    db: Session = Depends(get_db)
):
    return await AgentWorkflow.process_chat_turn(db, payload)

@router.get("/tools")
def get_registered_tools() -> List[Dict[str, Any]]:
    return AGENT_TOOLS_DEFINITIONS

@router.delete("/session/{session_id}")
async def reset_session(session_id: str):
    await redis_manager.delete(f"chat_history:{session_id}")
    return {"success": True, "message": f"Session {session_id} history cleared."}
