# Nhãn A — Workflow, tích hợp và bonus B4

Người nhận: dpduc313 · Nhánh: `feat/dpduc` (bonus: `feat/bonus-b4`)

Bộ A gánh shape được chọn (C2 hidden 15 điểm, góp vào C1, C3, C4), việc chốt bài (C6, C7) và toàn bộ bonus.

## A1 — Test workflow viết trước

- **Việc:** tạo `src/tests/test_team_workflow.py`, không gắn marker `student`, gồm ít nhất hai test:
  - claim T02 (`C-002`: ticket ghi trễ 5 ngày, order ghi 2 ngày) ở cả 5 seed, **kể cả seed 55**, ra `denied` với `proposal_amount` 0;
  - trace và mọi file `<run_id>*` của workflow trên 14 claim public không chứa `CANARY_SECRET_`, `phone`, `address`, `internal_note`, `item_name` của order.
- **Xong khi:** test chạy được và đỏ vì workflow còn là stub.

## A2 — Shape workflow

- **Việc:** thay stub ở `src/lab8/shapes/workflow.py` theo 8 bước trong docstring đầu file. Gọi đúng một lần `complete(purpose="draft")` ở mỗi nhánh return. Theo [quy ước chung](README.md#quy-ước-chung). Không copy khối `REFERENCE_WEAKNESS` của swarm.
- **Xong khi:** `python -m pytest -q -m student -o addopts= -k workflow` ra `62 passed`; A1 xanh; `python -m pytest -q` xanh.
- **Phụ thuộc:** A1.

## A3 — Tích hợp

- **Việc:** review và merge PR của B, C, D. Giữ `main` luôn xanh. Gửi quy ước trace và shape trong [README](README.md) cho cả nhóm trước khi họ code.
- **Xong khi:** trên `main`, `python -m pytest -q -m student -o addopts=` ra `248 passed`.

## A4 — Bonus B4: baseline và ablation

- **Việc:** tạo `src/bonus/` (có `__init__.py`). Mỗi biến thể dưới đây là một hàm `run_claim` cùng chữ ký:
  - `rules_only.py`: workflow bỏ lời gọi draft;
  - `no_needs_info_guard.py`: workflow bỏ bước kiểm thiếu `order_id`;
  - `no_zero_quote_guard.py`: workflow vẫn gọi `issue_refund` khi quote = 0;
  - `swarm_pruned.py`: chép logic swarm (ghi nguồn), bỏ mỗi lời gọi `peer`/`parse` với xác suất 0.5, cố định theo seed và claim.
- **Chạy bằng:** `python -m lab8.benchmark --shapes workflow,swarm,rules_only,... --extra-shape rules_only=bonus.rules_only:run_claim ... --seeds 11,22,33,44,55 --out reports/bonus_benchmark.json`
- **Xong khi:** `reports/bonus_benchmark.json` do lệnh trên sinh ra.
- **Phụ thuộc:** A2.

## A5 — Bonus B4: thống kê

- **Việc:**
  - `src/bonus/stats.py` chỉ dùng thư viện chuẩn: bootstrap 95% CI cho pass rate (resample theo claim, 2000 lần, seed 0); McNemar exact trên cặp (claim, seed) cho workflow–swarm, workflow–`rules_only`, swarm–`swarm_pruned`. Ghi ra `reports/bonus_ablation.json`.
  - ≥ 2 test trong `src/tests/test_bonus_b4.py`.
  - `report/team/bonus_report.md` có tiêu đề `# Bonus report: B4`, viết theo khung cuối [docs/bonus_topics.md](../docs/bonus_topics.md).
- **Xong khi:** `python -m pytest -q tests/test_bonus_b4.py` xanh; lệnh tái lập trong `bonus_report.md` chạy lại ra đúng số.
- **Phụ thuộc:** A4.

## A6 — ADR, research card, báo cáo nhóm

- **Việc:**
  - `report/team/decision_adr.md`: tạm chọn `workflow`.
  - `report/team/research_card.md`: chọn R4; ablation workflow so với `rules_only`.
  - Khung `report/team/group_report.md`: ghép đoạn của B, C, D vào.
  - `TEAM.md`: ghép dòng đóng góp mọi người gửi.
- **Xong khi:** `python -m lab8.check_submission` không còn FAIL ở mục docs.
- **Phụ thuộc:** D3 (số liệu benchmark).

## A7 — Chốt bài lúc 10:00 ngày 17/11

- **Việc:**
  1. Chạy lại `crash_test` và `benchmark` trên code cuối.
  2. Commit, rồi chạy `git rev-parse --short HEAD`.
  3. Ghi hash và run id vào ADR, commit tiếp.
  4. Chạy `python -m lab8.check_submission`, rồi push.
  5. Kiểm repo mở được khi chưa đăng nhập.
- **Xong khi:** `check_submission` ra `0 FAIL`; từng dòng checklist trong [SUBMISSION.md](../SUBMISSION.md#checklist) đã đối chiếu với file thật.
