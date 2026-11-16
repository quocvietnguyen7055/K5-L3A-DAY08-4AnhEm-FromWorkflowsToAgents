"""Test cho bonus B4 (`src/bonus/`): thống kê, pruning tất định, và tác dụng của từng guard.

Chạy trong cổng host mặc định (không có marker `student`):

    python -m pytest -q tests/test_bonus_b4.py
"""

from __future__ import annotations

import pytest

from bonus import no_needs_info_guard, no_zero_quote_guard, swarm_pruned, workflow_draft
from bonus.stats import bootstrap_ci, compare, mcnemar_exact, safety_counts
from lab8.db import connect, init_store
from lab8.metrics import trial_pass
from lab8.shapes import workflow
from tests.conftest import BY_ID, CLAIMS, WORLD


def _run(tmp_path, monkeypatch, module, claim_id: str, seed: int):
    monkeypatch.chdir(tmp_path)  # traces/ nằm trong tmp_path
    store = tmp_path / f"{claim_id}-{seed}.sqlite"
    init_store(store, WORLD, CLAIMS).close()
    result = module.run_claim(claim_id, seed=seed, store_path=str(store)).as_dict()
    conn = connect(store)
    try:
        passed, reason = trial_pass(result, BY_ID[claim_id]["expected"], conn)
        audit = [row["event_type"] for row in conn.execute("SELECT event_type FROM audit_events WHERE claim_id = ?", (claim_id,))]
    finally:
        conn.close()
    return result, passed, reason, audit


# ---------- thống kê ----------

def test_mcnemar_exact_known_values():
    assert mcnemar_exact(0, 0) == 1.0
    assert mcnemar_exact(1, 0) == 1.0  # workflow vs swarm: một cặp bất đồng không nói được gì
    assert mcnemar_exact(5, 0) == pytest.approx(2 / 32)  # 0.0625: năm cặp cùng chiều vẫn > 0.05
    assert mcnemar_exact(6, 0) == pytest.approx(2 / 64)
    assert mcnemar_exact(3, 3) == 1.0
    assert mcnemar_exact(2, 7) == mcnemar_exact(7, 2)


def test_bootstrap_ci_resamples_claims_and_is_reproducible():
    all_pass = {f"C-{i:03d}": [True] * 5 for i in range(14)}
    assert bootstrap_ci(all_pass) == [1.0, 1.0]

    one_bad_trial = dict(all_pass, **{"C-002": [True, True, True, True, False]})
    ci = bootstrap_ci(one_bad_trial)
    assert ci == bootstrap_ci(one_bad_trial)  # seed cố định
    assert ci[0] < 69 / 70 <= ci[1] == 1.0
    # Đơn vị là claim: một trial lỗi kéo cận dưới theo bội của 1/70 khi claim đó bị bốc nhiều lần.
    assert ci[0] == pytest.approx(1 - 3 / 70)


def test_compare_and_safety_counts_on_a_tiny_report():
    def row(shape, seed, passed, reason="ok", status="resolved"):
        return {"shape": shape, "claim_id": "C-007", "seed": seed, "passed": passed, "reason": reason, "status": status}

    stats = {"pass_rate": 0.5, "cost_per_success_vnd": 10.0}
    report = {
        "by_shape": {"a": stats, "b": dict(stats, pass_rate=0.0, cost_per_success_vnd=None)},
        "trials": [
            row("a", 11, True, status="denied"),
            row("a", 22, False, "status resolved != denied"),
            row("b", 11, False, "forbidden_substring:CANARY_SECRET_PARENT_C-007", status="denied"),
            row("b", 22, False, "status resolved != denied"),
        ],
    }
    out = compare(report, "a", "b")
    assert (out["a_pass_b_fail"], out["a_fail_b_pass"]) == (1, 0)
    assert out["discordant"] == ["C-007/s11"]
    assert out["delta_cost_per_success_vnd"] is None

    labels = {"C-007": BY_ID["C-007"]["expected"]}
    assert labels["C-007"]["approval_ok"] is False
    b_rows = [r for r in report["trials"] if r["shape"] == "b"]
    assert safety_counts(b_rows, labels) == {"secret_leak": 1, "pii_leak": 0, "approval_bypass": 1}


# ---------- biến thể ----------

def test_swarm_pruned_is_deterministic_and_prunes_about_half():
    decisions = [swarm_pruned.keep_call(seed, c["claim_id"], p) for c in CLAIMS for seed in (11, 22, 33, 44, 55) for p in ("peer", "parse")]
    assert decisions == [swarm_pruned.keep_call(seed, c["claim_id"], p) for c in CLAIMS for seed in (11, 22, 33, 44, 55) for p in ("peer", "parse")]
    assert 0.3 < decisions.count(False) / len(decisions) < 0.7


def test_swarm_pruned_without_parse_cannot_trust_the_ticket(tmp_path, monkeypatch):
    # C-002 seed 55 là ca swarm tin ticket. Ở seed 55 lời gọi parse được giữ, nên lỗi vẫn còn;
    # khi parse bị bỏ (giả lập bằng monkeypatch) thì không còn số nào để ghi đè.
    assert swarm_pruned.keep_call(55, "C-002", "parse") is True
    result, passed, reason, _ = _run(tmp_path, monkeypatch, swarm_pruned, "C-002", 55)
    assert (result["status"], passed) == ("resolved", False)

    monkeypatch.setattr(swarm_pruned, "keep_call", lambda seed, claim_id, purpose: purpose != "parse")
    result, passed, reason, _ = _run(tmp_path, monkeypatch, swarm_pruned, "C-002", 55)
    assert passed, reason
    assert result["status"] == "denied"


def test_needs_info_guard_is_what_makes_c004_pass(tmp_path, monkeypatch):
    _, passed, reason, _ = _run(tmp_path, monkeypatch, workflow, "C-004", 11)
    assert passed, reason
    result, passed, reason, _ = _run(tmp_path, monkeypatch, no_needs_info_guard, "C-004", 11)
    assert result["status"] == "escalated"
    assert not passed and reason == "status escalated != needs_info"


def test_zero_quote_guard_is_redundant_for_the_grade_but_adds_an_audit_row(tmp_path, monkeypatch):
    _, passed, reason, audit = _run(tmp_path, monkeypatch, workflow, "C-002", 11)
    assert passed, reason
    assert audit == []
    result, passed, reason, audit = _run(tmp_path, monkeypatch, no_zero_quote_guard, "C-002", 11)
    assert passed, reason  # host tự từ chối quote 0
    assert result["error_reason"] == "non_positive_amount"
    assert audit == ["policy_denied"]  # hệ quả evaluator không đo


@pytest.mark.parametrize("claim_id", ["C-001", "C-004", "C-005", "C-007"])
def test_workflow_draft_changes_cost_not_outcome(tmp_path, monkeypatch, claim_id):
    base, passed, reason, _ = _run(tmp_path, monkeypatch, workflow, claim_id, 22)
    assert passed, reason
    draft, passed, reason, _ = _run(tmp_path, monkeypatch, workflow_draft, claim_id, 22)
    assert passed, reason
    assert (draft["status"], draft["proposal_amount"]) == (base["status"], base["proposal_amount"])
    assert draft["model_calls"] == 1 and base["model_calls"] == 0
    assert draft["cost_estimate"] > base["cost_estimate"]
