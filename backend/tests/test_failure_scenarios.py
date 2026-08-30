import pytest
from backend.app.services.failure_simulation import FailureSimulationService

def test_simulate_stock_out(db_session):
    res = FailureSimulationService.simulate_stock_out(db_session, session_id="test_stockout_sess")
    assert res["scenario"] == "STOCK_OUT_RACE_CONDITION"
    assert len(res["recommended_substitutes"]) >= 1

def test_simulate_prompt_injection_discount(db_session):
    res = FailureSimulationService.simulate_prompt_injection_discount_exploit(db_session, session_id="test_injection_sess")
    assert res["scenario"] == "PROMPT_INJECTION_DISCOUNT_EXPLOIT"
    assert res["policy_gate_blocked"] is True

def test_simulate_price_hallucination(db_session):
    res = FailureSimulationService.simulate_price_hallucination(db_session, session_id="test_hallucination_sess")
    assert res["scenario"] == "AGENT_PRICE_HALLUCINATION"
    assert res["price_integrity_gate_blocked"] is True
