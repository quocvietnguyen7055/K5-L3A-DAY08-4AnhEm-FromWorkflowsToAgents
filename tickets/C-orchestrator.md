# Nhãn C — Shape orchestrator và handoff

Người nhận: (tự điền) · Nhánh: `feat/<tên-github>`

Bộ C giữ trọn **C5 — Handoff và trace an toàn (10 điểm)**, vì bằng chứng của C5 là `src/lab8/shapes/orchestrator.py`. Bộ C cũng góp vào C1. Lộ `CANARY_SECRET_*` là vi phạm must-pass, không bù được bằng điểm khác.

Đọc trước:

- docstring đầu `src/lab8/shapes/orchestrator.py`;
- `src/lab8/handoff.py` (`make_handoff`, allowlist `ALLOWED_FIELDS`, `FACT_KEYS`);
- `src/lab8/runtime.py` (`run_readonly_investigators`);
- `src/lab8/shapes/swarm_reference.py`, đoạn từ `make_handoff` tới `issue_refund`;
- [docs/architecture.md](../docs/architecture.md#handoff) và [docs/contracts.md](../docs/contracts.md#trace-contract-v1).

## C1 — Shape orchestrator

- **Việc:** thay stub ở `src/lab8/shapes/orchestrator.py`:
  - Dựng handoff bằng `make_handoff(request_id=f"REQ-{claim_id}", claim_id=claim_id, task=..., facts={}, allowed_tools=["lookup_order", "lookup_policy", "compute_compensation"])`.
  - Không đưa `parent_secret`, `raw_headers`, ticket hay nguyên claim row vào `facts`. Tóm tắt bằng LLM **không** tính là redaction.
  - Chạy `run_readonly_investigators(conn, budget, handoff, principal_id=...)`. Investigator chỉ có tool đọc.
  - Thiếu `order_id` thì trả `needs_info`. Order không `visible` thì trả `escalated`.
  - Orchestrator lấy quote từ kết quả `compute_compensation` của investigator, rồi tự gọi `durability.issue_refund(conn, claim_id, <quote đầy đủ>, crash_at=crash_at)`.
  - **Không** có khối ghi đè `delay_days` bằng số trong ticket (đó là điểm yếu cố ý của swarm).
  - Trace ghi `handoff` bằng `safe_dump(handoff)` (bản đã sanitize), không ghi parent context.
  - Theo [quy ước chung](README.md#quy-ước-chung) về status, trace và crash.
- **Xong khi:** `python -m pytest -q -m student -o addopts= -k orchestrator` ra `62 passed`, và `python -m pytest -q` vẫn xanh.

## C2 — Test của C

- **Việc:** tạo `src/tests/test_team_orchestrator.py` (không gắn marker `student`), ít nhất một test. Gợi ý:
  - chạy orchestrator trên 14 claim public, đọc trace, kiểm event `handoff` chỉ có khóa thuộc `ALLOWED_FIELDS`, `allowed_tools` không chứa tool ghi, và cả file trace không chứa `CANARY_SECRET_`, `raw_headers`, `parent_secret`;
  - T02 (`C-002`) ở seed 55 vẫn ra `denied`.
- **Xong khi:** `python -m pytest -q` xanh, có test mới.

## C3 — Báo cáo của C

- **Việc:**
  - Gửi A đoạn cho mục 3 "Giải pháp" của `group_report.md`: orchestrator chuyển gì cho investigator, handoff được sanitize ra sao.
  - Gửi A đoạn cho mục "Trace và bằng chứng" của ADR: trace ghi event nào, field nào cố ý **không** ghi và vì sao.
  - Làm báo cáo cá nhân và gửi dòng đóng góp, theo [việc của mọi người](README.md#việc-của-mọi-người-ngoài-bộ-ticket).
- **Xong khi:** A đã nhận hai đoạn văn; file cá nhân của bạn đã có trong PR.
