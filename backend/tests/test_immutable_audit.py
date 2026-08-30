import pytest
from sqlalchemy import select
from backend.app.models.audit import AuditLog
from backend.app.services.audit_service import AuditService

def test_audit_chain_integrity_and_tamper_detection(db_session):
    AuditService.log_financial_decision(
        db=db_session,
        actor="AGENT",
        action_type="OFFER_RECOMMENDED",
        payload={"offer_code": "SAVE10", "potential_savings": 500}
    )
    AuditService.log_financial_decision(
        db=db_session,
        actor="USER",
        action_type="CART_CHECKOUT_INITIATED",
        payload={"amount": 4500}
    )
    AuditService.log_financial_decision(
        db=db_session,
        actor="SYSTEM",
        action_type="PAYMENT_VERIFIED",
        payload={"amount": 4500, "status": "PAID"}
    )

    # 1. Verify clean chain
    res_clean = AuditService.verify_audit_chain(db_session)
    assert res_clean.is_valid is True
    assert res_clean.total_blocks >= 4

    # 2. Tamper with a block payload in database
    stmt = select(AuditLog).where(AuditLog.sequence_index == 2)
    block_2 = db_session.execute(stmt).scalars().first()
    block_2.payload = {"tampered": "illegal_price_manipulation"}
    db_session.commit()

    # 3. Verify that the verifier detects the tampering mathematically
    res_tampered = AuditService.verify_audit_chain(db_session)
    assert res_tampered.is_valid is False
    assert res_tampered.broken_block_index == 2
