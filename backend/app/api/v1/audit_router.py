from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.audit_schema import AuditLogResponse, AuditChainVerificationResult
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["Immutable Financial Audit Ledger"])

@router.get("/logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    return AuditService.get_logs(db, limit=limit, offset=offset)

@router.get("/verify-chain", response_model=AuditChainVerificationResult)
def verify_hash_chain(db: Session = Depends(get_db)):
    """Mathematically audits the entire SHA-256 cryptographic hash chain across all blocks."""
    return AuditService.verify_audit_chain(db)
