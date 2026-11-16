"""Ablation B4 (c): workflow bỏ bước dừng khi quote = 0.

Nguồn: `src/lab8/shapes/workflow.py` của nhóm. Khác bản gốc đúng một chỗ: khi
`compute_compensation` trả 0, shape vẫn gọi `issue_refund` với số 0 và để host quyết định.
Câu hỏi: guard ở shape có thừa khi host đã có cổng approval và trần theo đơn không?
"""

from __future__ import annotations

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.schemas import Budget, make_run_id
from lab8.shapes.common import finish
from lab8.tools import compute_compensation, get_claim_view, lookup_order, tool_cost
from lab8.trace import Trace

SHAPE = "no_zero_quote_guard"


def run_claim(claim_id: str, *, seed: int, store_path: str, crash_at: str | None = None):
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run(conn, claim_id: str, *, seed: int, crash_at: str | None):
    budget = Budget()
    trace = Trace(make_run_id(SHAPE, claim_id, seed))

    def done(status: str, proposal: int, reason: str | None = None):
        return finish(conn, shape=SHAPE, claim_id=claim_id, seed=seed, status=status, proposal_amount=proposal, budget=budget, trace=trace, error_reason=reason)

    budget.add_tool(tool_cost())
    claim = get_claim_view(conn, claim_id)
    trace.add("claim", {k: claim[k] for k in ("found", "claim_id", "order_id") if k in claim})
    if not claim.get("found"):
        return done("failed", 0, "unknown_claim")
    if not claim.get("order_id"):
        trace.add("decision", {"status": "needs_info"})
        return done("needs_info", 0, "missing_order_id")

    budget.add_tool(tool_cost())
    order_view = lookup_order(conn, claim["order_id"], claim["principal_id"])
    if not order_view.get("visible"):
        trace.add("order", {"visible": False, "reason": order_view.get("reason")})
        return done("escalated", 0, order_view.get("reason"))
    trace.add("order", order_view)

    budget.add_tool(tool_cost())
    quote = compute_compensation(conn, order_view["order"])
    proposal = int(quote["amount_vnd"])
    trace.add("quote", quote)
    # Ablation: không có guard `if proposal <= 0: denied`; quote 0 vẫn đi tới host.

    try:
        result = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise
    if not result["ok"]:
        return done("failed" if result["conflict"] else "denied", proposal, result["reason"])
    return done("resolved", proposal)
