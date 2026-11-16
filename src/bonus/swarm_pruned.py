"""Baseline B4 "swarm pruned": swarm tham chiếu, bỏ ngẫu nhiên các lời gọi `peer` và `parse`.

Nguồn: chép từ `src/lab8/shapes/swarm_reference.py` (repo đề VinUni-AI20k, commit 034c6c4).
Ý tưởng theo claim của *Rethinking Evaluation of MAS Efficiency* (EMNLP 2026): random pruning
có lúc vẫn giữ được hiệu năng.

Khác bản gốc:
- Mỗi lời gọi `peer` và `parse` bị bỏ với xác suất 0.5. Quyết định cố định theo
  SHA-256 của `(seed, claim_id, purpose)`, nên chạy lại ra y hệt (không dùng `hash()` của
  Python vì `str` hash đổi theo tiến trình).
- Số ngày parse từ ticket lấy từ **kết quả** lời gọi `parse`. Bỏ lời gọi `parse` thì swarm
  không có số đó, nên khối tin ticket (`REFERENCE_WEAKNESS`) không kích hoạt được.
- Trace thêm sự kiện `pruned` ghi lời gọi nào bị bỏ (chỉ cờ true/false, không có nội dung ticket).
Mọi thứ khác giữ nguyên: handoff, investigator, `draft`, cách gọi host.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.handoff import make_handoff
from lab8.mock_llm import complete
from lab8.runtime import run_readonly_investigators
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import compute_compensation, tool_cost
from lab8.trace import Trace

SHAPE = "swarm_pruned"
PRUNE_P = 0.5


def keep_call(seed: int, claim_id: str, purpose: str) -> bool:
    """True nếu lời gọi được giữ. Tất định theo (seed, claim_id, purpose)."""
    digest = hashlib.sha256(f"{seed}|{claim_id}|{purpose}".encode()).digest()
    return digest[0] / 256 >= PRUNE_P


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run(conn: sqlite3.Connection, claim_id: str, *, seed: int, crash_at: str | None) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id(SHAPE, claim_id, seed))
    budget.add_tool(tool_cost())
    claim_row = conn.execute(
        "SELECT claim_id, principal_id, order_id, ticket FROM claims WHERE claim_id = ?",
        (claim_id,),
    ).fetchone()
    if claim_row is None:
        trace.add("error", {"reason": "unknown_claim"})
        return _finish(conn, claim_id, seed, "failed", 0, budget, trace, "unknown_claim")

    ticket = claim_row["ticket"]
    keep_peer = keep_call(seed, claim_id, "peer")
    keep_parse = keep_call(seed, claim_id, "parse")
    trace.add("pruned", {"peer": not keep_peer, "parse": not keep_parse})
    if keep_peer:
        complete(budget, seed=seed, purpose="peer", prompt=ticket)
    parsed_delay = None
    if keep_parse:
        parsed_text = complete(budget, seed=seed, purpose="parse", prompt=ticket)
        match = re.fullmatch(r"parsed_delay=(\d+)", parsed_text)
        parsed_delay = int(match.group(1)) if match else None

    if not claim_row["order_id"]:
        complete(budget, seed=seed, purpose="draft", prompt="needs_info")
        trace.add("decision", {"status": "needs_info"})
        return _finish(conn, claim_id, seed, "needs_info", 0, budget, trace, "missing_order_id")

    handoff = make_handoff(
        request_id=f"REQ-{claim_id}",
        claim_id=claim_id,
        task="check_applicable_policy",
        facts={},
        allowed_tools=["lookup_order", "lookup_policy", "compute_compensation"],
    )
    trace.add("handoff", safe_dump(handoff))
    investigated = run_readonly_investigators(conn, budget, handoff, principal_id=claim_row["principal_id"])
    order_view = investigated["tools"].get("lookup_order", {})
    trace.add("investigator", {
        "lookup_order": order_view,
        "policy_count": len((investigated["tools"].get("lookup_policy") or {}).get("policies") or []),
    })
    if not order_view.get("visible"):
        complete(budget, seed=seed, purpose="draft", prompt="escalated")
        return _finish(conn, claim_id, seed, "escalated", 0, budget, trace, order_view.get("reason"))

    order = dict(order_view["order"])
    # REFERENCE_WEAKNESS giữ nguyên như swarm: chỉ kích hoạt được khi lời gọi parse không bị bỏ.
    if parsed_delay is not None and parsed_delay != int(order["delay_days"]) and seed % 5 == 0:
        order["delay_days"] = parsed_delay
        trace.add("model_override", {"delay_days": parsed_delay})

    quote_payload = investigated["tools"]["compute_compensation"]
    if order["delay_days"] != order_view["order"]["delay_days"]:
        budget.add_tool(tool_cost())
        quote_payload = compute_compensation(conn, order)
    proposal = int(quote_payload["amount_vnd"])
    trace.add("quote", quote_payload)
    complete(budget, seed=seed, purpose="draft", prompt=f"proposal={proposal}")

    if proposal <= 0:
        return _finish(conn, claim_id, seed, "denied", 0, budget, trace, quote_payload.get("reason"))

    try:
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise

    if not outcome["ok"]:
        status = "failed" if outcome["conflict"] else "denied"
        return _finish(conn, claim_id, seed, status, proposal, budget, trace, outcome["reason"])
    return _finish(conn, claim_id, seed, "resolved", proposal, budget, trace, None)


def _finish(conn, claim_id, seed, status, proposal, budget, trace, reason) -> RunResult:
    return finish(
        conn,
        shape=SHAPE,
        claim_id=claim_id,
        seed=seed,
        status=status,
        proposal_amount=proposal,
        budget=budget,
        trace=trace,
        error_reason=reason,
    )
