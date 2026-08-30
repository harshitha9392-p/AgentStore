from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class AuditLogResponse(BaseModel):
    id: str
    sequence_index: int
    timestamp: str
    session_id: Optional[str] = None
    order_id: Optional[str] = None
    actor: str
    action_type: str
    payload: Dict[str, Any]
    decision_rationale: Optional[str] = None
    previous_hash: str
    block_hash: str

class AuditChainVerificationResult(BaseModel):
    is_valid: bool
    total_blocks: int
    verified_blocks: int
    broken_block_index: Optional[int] = None
    details: str
