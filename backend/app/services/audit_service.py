from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from backend.app.models.audit import AuditLog
from backend.app.core.security import compute_audit_hash
from backend.app.schemas.audit_schema import AuditLogResponse, AuditChainVerificationResult

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

class AuditService:
    @staticmethod
    def log_financial_decision(
        db: Session,
        actor: str,
        action_type: str,
        payload: Dict[str, Any],
        decision_rationale: Optional[str] = None,
        session_id: Optional[str] = None,
        order_id: Optional[str] = None
    ) -> AuditLog:
        """Appends an immutable, SHA-256 cryptographically chained record to the financial audit ledger."""
        stmt = select(AuditLog).order_by(desc(AuditLog.sequence_index)).limit(1)
        latest_block = db.execute(stmt).scalar_one_or_none()

        if latest_block is None:
            previous_hash = GENESIS_HASH
            sequence_index = 1
        else:
            previous_hash = latest_block.block_hash
            sequence_index = latest_block.sequence_index + 1

        timestamp_iso = datetime.now(timezone.utc).isoformat()

        block_hash = compute_audit_hash(
            previous_hash=previous_hash,
            timestamp_iso=timestamp_iso,
            actor=actor,
            action=action_type,
            payload=payload
        )

        audit_entry = AuditLog(
            sequence_index=sequence_index,
            timestamp_iso=timestamp_iso,
            session_id=session_id,
            order_id=order_id,
            actor=actor,
            action_type=action_type,
            payload=payload,
            decision_rationale=decision_rationale,
            previous_hash=previous_hash,
            block_hash=block_hash
        )

        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry

    @staticmethod
    def verify_audit_chain(db: Session) -> AuditChainVerificationResult:
        """Verifies mathematical validity of every block in the hash chain."""
        stmt = select(AuditLog).order_by(AuditLog.sequence_index.asc())
        blocks = db.execute(stmt).scalars().all()

        if not blocks:
            return AuditChainVerificationResult(
                is_valid=True,
                total_blocks=0,
                verified_blocks=0,
                broken_block_index=None,
                details="Audit ledger is empty. Chain is clean."
            )

        expected_prev_hash = GENESIS_HASH
        for idx, block in enumerate(blocks):
            if block.previous_hash != expected_prev_hash:
                return AuditChainVerificationResult(
                    is_valid=False,
                    total_blocks=len(blocks),
                    verified_blocks=idx,
                    broken_block_index=block.sequence_index,
                    details=f"Hash chain broken at block sequence {block.sequence_index}: Previous hash mismatch!"
                )

            recalculated_hash = compute_audit_hash(
                previous_hash=block.previous_hash,
                timestamp_iso=block.timestamp_iso,
                actor=block.actor,
                action=block.action_type,
                payload=block.payload
            )

            if recalculated_hash != block.block_hash:
                return AuditChainVerificationResult(
                    is_valid=False,
                    total_blocks=len(blocks),
                    verified_blocks=idx,
                    broken_block_index=block.sequence_index,
                    details=f"Block payload tampered at sequence {block.sequence_index}: Computed hash {recalculated_hash[:12]} != Stored hash {block.block_hash[:12]}"
                )

            expected_prev_hash = block.block_hash

        return AuditChainVerificationResult(
            is_valid=True,
            total_blocks=len(blocks),
            verified_blocks=len(blocks),
            broken_block_index=None,
            details=f"All {len(blocks)} financial audit blocks cryptographically verified with zero discrepancies."
        )

    @staticmethod
    def get_logs(db: Session, limit: int = 50, offset: int = 0) -> List[AuditLogResponse]:
        stmt = select(AuditLog).order_by(desc(AuditLog.sequence_index)).limit(limit).offset(offset)
        logs = db.execute(stmt).scalars().all()

        return [
            AuditLogResponse(
                id=log.id,
                sequence_index=log.sequence_index,
                timestamp=log.timestamp_iso,
                session_id=log.session_id,
                order_id=log.order_id,
                actor=log.actor,
                action_type=log.action_type,
                payload=log.payload,
                decision_rationale=log.decision_rationale,
                previous_hash=log.previous_hash,
                block_hash=log.block_hash
            )
            for log in logs
        ]
