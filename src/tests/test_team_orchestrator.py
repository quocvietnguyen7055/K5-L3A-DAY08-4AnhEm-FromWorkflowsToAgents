"""Team C regression tests for orchestrator handoff and trace safety."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lab8.db import init_store
from lab8.handoff import ALLOWED_FIELDS, READONLY_TOOLS, WRITE_TOOLS
from lab8.shapes.orchestrator import run_claim
from tests.conftest import CLAIMS, WORLD


@pytest.mark.parametrize("claim", CLAIMS, ids=lambda claim: claim["claim_id"])
def test_public_orchestrator_handoff_and_trace_are_safe(tmp_path, monkeypatch, claim):
    monkeypatch.chdir(tmp_path)
    store = tmp_path / f"orchestrator-{claim['claim_id']}.sqlite"
    init_store(store, WORLD, CLAIMS).close()

    result = run_claim(claim["claim_id"], seed=11, store_path=str(store))
    trace_path = Path(result.trace_path)
    trace = json.loads(trace_path.read_text(encoding="utf-8"))

    assert trace["run_id"] == result.run_id
    assert isinstance(trace["events"], list)
    handoffs = [event["payload"] for event in trace["events"] if event["kind"] == "handoff"]
    if claim.get("order_id"):
        assert len(handoffs) == 1
    else:
        assert handoffs == []

    for handoff in handoffs:
        assert set(handoff) <= ALLOWED_FIELDS
        tools = set(handoff["allowed_tools"])
        assert tools <= READONLY_TOOLS
        assert not tools & WRITE_TOOLS

    trace_text = trace_path.read_text(encoding="utf-8")
    for forbidden in ("CANARY_SECRET_", "raw_headers", "parent_secret"):
        assert forbidden not in trace_text


def test_t02_seed_55_is_denied_from_order_data(public_db, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = run_claim("C-002", seed=55, store_path=str(public_db))

    assert result.status == "denied"
    assert result.proposal_amount == 0
    assert result.refund_effects == []
