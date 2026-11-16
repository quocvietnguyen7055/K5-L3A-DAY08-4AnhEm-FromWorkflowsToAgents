# Nhãn B — Shape single (một agent ReAct)

Người nhận: (tự điền) · Nhánh: `feat/<tên-github>`

Shape B góp vào C1 (20 điểm, chia cho 3 shape) và các test T11, T12, T13, T14 của shape single.

Đọc trước:

- docstring đầu `src/lab8/shapes/single.py`;
- `src/lab8/runtime.py` (`run_react`, `dispatch`);
- `src/lab8/shapes/swarm_reference.py`, để xem cách gọi `finish`, `issue_refund` và xử lý crash;
- [docs/business_rules.md](../docs/business_rules.md) và [docs/contracts.md](../docs/contracts.md).

## B1 — Shape single

- **Việc:** thay stub ở `src/lab8/shapes/single.py`:
  - Viết `decide(observation)`. Hàm này chọn tool đọc theo thứ tự `get_claim_view` → `lookup_order` → `compute_compensation` → `{"final": ...}`. Mỗi bước gọi một lần `complete(purpose="react")` để tính cost của vòng ReAct.
  - `decide` không bao giờ trả `issue_refund`; `dispatch` sẽ từ chối tool ghi.
  - Không đọc số ngày trễ trong ticket. Chỉ dùng `delay_days` của order.
  - Chạy `lab8.runtime.run_react(conn, budget, observation=..., decide=decide, max_steps=8)`.
  - Sau vòng lặp, **code của shape** (không phải model) gọi `durability.issue_refund(conn, claim_id, <quote đầy đủ>, crash_at=crash_at)`.
  - Nhánh `step_cap` trả `failed` và vẫn ghi trace.
  - Theo [quy ước chung](README.md#quy-ước-chung) về status, trace và crash.
- **Lưu ý:** sau mỗi bước, `run_react` chỉ đưa lại cho `decide` ba thứ: `last_tool`, `last_result` và `claim` của observation ban đầu. Order view của bước trước sẽ mất. Muốn nhớ nó qua các bước thì giữ trong biến bên ngoài `decide`, ví dụ một closure.
- **Xong khi:** `python -m pytest -q -m student -o addopts= -k single` ra `62 passed`, và `python -m pytest -q` vẫn xanh.

## B2 — Test của B

- **Việc:** tạo `src/tests/test_team_single.py` (không gắn marker `student`), ít nhất một test. Gợi ý:
  - T02 (`C-002`) ở seed 55 vẫn ra `denied` với proposal 0, tức single không tin ticket;
  - chạy single trên một claim bất kỳ, rồi kiểm `model_calls` ≤ 8 và trace có `run_id` khớp kết quả.
- **Xong khi:** `python -m pytest -q` xanh, có test mới.

## B3 — Báo cáo của B

- **Việc:**
  - Gửi A một đoạn ngắn cho mục 3 "Giải pháp" của `group_report.md`: single đọc gì, model quyết gì, code quyết gì, vì sao model không chọn số tiền.
  - Làm báo cáo cá nhân và gửi dòng đóng góp, theo [việc của mọi người](README.md#việc-của-mọi-người-ngoài-bộ-ticket).
- **Xong khi:** A đã nhận đoạn văn; file cá nhân của bạn đã có trong PR.
