# Nhãn D — Ledger, crash và đánh giá

Người nhận: (tự điền) · Nhánh: `feat/<tên-github>`

Bộ D canh **C3 — Durability (20 điểm)**, 3 điều kiện must-pass và số liệu cho C6. D không viết shape. D chạy lệnh, soi kết quả và báo lỗi về đúng người. Bộ này làm được ngay từ đầu buổi.

Đọc trước:

- `src/lab8/durability.py` (idempotency key `refund:{claim_id}`, các điểm `crash_at`);
- `src/lab8/crash_test.py`;
- `src/tests/test_public_matrix.py` (T11, T12);
- [docs/metrics.md](../docs/metrics.md) và [docs/business_rules.md](../docs/business_rules.md).

## D1 — Hiểu và demo durability

- **Việc:**
  - Chạy `python -m lab8.demo.buggy_workflow` để xem vì sao checkpoint đơn lẻ không thay được ledger.
  - Chạy thử crash rồi resume với swarm:
    `python -m lab8.run --shape swarm --claim-id C-012 --seed 11 --db data/crash.sqlite --crash-at after_effect_before_checkpoint`,
    rồi chạy lại cùng lệnh nhưng bỏ `--crash-at`.
  - Ghi lại mỗi lần chạy có mấy refund và mấy audit `refund_committed`.
- **Xong khi:** giải thích được cho cả nhóm 3 điểm crash `before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`.

## D2 — Crash suite và T11/T12 cho cả 3 shape

- **Việc:**
  - Chạy `python -m lab8.crash_test --count 20 --out reports/crash.json`.
  - Mỗi khi B, C hoặc A mở PR, checkout nhánh đó và chạy `python -m pytest -q -m student -o addopts= -k "t11 or t12"`. Fail thì comment vào PR, ghi rõ test nào và output.
- **Lưu ý:** `crash_test` chỉ kiểm host và swarm. Crash của shape nhóm chỉ được chứng minh qua T12, nên phải chạy T12 cho từng shape.
- **Xong khi:** `crash.json` có `crash_safety` = `20/20`; T11 và T12 xanh ở workflow, single, orchestrator.

## D3 — Benchmark và tự kiểm hidden

- **Việc:**
  - Sau khi 3 shape đã merge vào `main`, chạy:
    `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`
  - Lấy ra bảng theo shape: pass rate, pass^5, seed min–max, variance, cost/success, mean/p95 steps. Gửi A cả bảng lẫn `run_id`.
  - Sau 16:15, giảng viên phát `student_drop/`. Đặt thư mục đó trong `src/` rồi chạy lệnh ở [src/README.md](../src/README.md#tự-kiểm-trên-bộ-hidden-cp5) để ra `reports/hidden_selfcheck.json`.
- **Lưu ý:**
  - File nộp chính thức do A chạy lại ở commit chốt. Bản của D dùng để rà số và viết báo cáo.
  - Không sửa tay JSON.
  - Không commit `student_drop/`.
- **Xong khi:** A đã nhận bảng số; `hidden_selfcheck.json` không có trial `status` = `error` hay `leak_suspect`.

## D4 — Test của D: quét lộ dữ liệu

- **Việc:** tạo `src/tests/test_team_leak_scan.py` (không gắn marker `student`), ít nhất một test:
  - chạy 3 shape nhóm trên 14 claim public;
  - kiểm trace, mọi file `<run_id>*` cùng thư mục và JSON kết quả không chứa chuỗi nào trong `expected.forbid_substrings` của claim, cũng không chứa `phone`, `address`, `internal_note`, `item_name` của các order trong `data/public_world_state.json`.
- **Lưu ý:** test này dùng để bắt lỗi của B và C, nên có thể đỏ cho tới khi cả 3 shape xong. Merge nó vào `main` **sau** khi 3 shape đã xanh, để cổng host không đỏ.
- **Xong khi:** `python -m pytest -q` xanh trên `main` khi đã có test này.

## D5 — Báo cáo của D

- **Việc:**
  - Gửi A mục 4 "Kết quả" của `group_report.md`: bảng 4 shape lấy từ `benchmark.json`, crash safety lấy từ `crash.json`, kết quả tự kiểm hidden. Không chép số tay từ terminal.
  - Làm báo cáo cá nhân và gửi dòng đóng góp, theo [việc của mọi người](README.md#việc-của-mọi-người-ngoài-bộ-ticket).
- **Xong khi:** A đã nhận mục 4; file cá nhân của bạn đã có trong PR.
