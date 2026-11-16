# Báo cáo cá nhân — Nguyen Quoc Viet

## 1. Thông tin thành viên

- Họ tên: Nguyen Quoc Viet
- MSSV: 2A202603556
- Email: rinthongminh@gmail.com
- GitHub: [quocvietnguyen7055](https://github.com/quocvietnguyen7055)
- Vai trò: Nhóm trưởng

## 2. Phần việc phụ trách

Nhóm trưởng; phần C: shape orchestrator và handoff an toàn. Cùng nhóm hoàn thiện phần tích hợp và báo cáo.

## 3. Đóng góp cụ thể

Đóng góp liên quan phần C gồm triển khai shape orchestrator trong commit `3614266` và kiểm thử trong commit `01bdac2`.

## 4. Bằng chứng

- `python -m pytest -q`: 54 passed.
- `python -m pytest -q -m student -o addopts=`: 248 passed.
- `python -m pytest -q tests/test_team_orchestrator.py`: 15 passed.
- `python -m pytest -q`: 146 passed.
- `python -m lab8.crash_test --count 20 --out reports/crash.json`: crash safety 20/20.
- `python -m lab8.check_submission`: 0 FAIL, 0 WARN.
- Run benchmark ví dụ: `R-workflow-C-001-s11`.

## 5. Công cụ AI đã dùng

ChatGPT hỗ trợ triển khai mã, soạn báo cáo và rà soát kết quả. Nhóm đối chiếu mã với contract của lab và chạy các lệnh kiểm tra nêu trên. Thành viên cần nắm được cách tính quote, ranh giới quyền ghi của host và cách handoff được lọc.

## 6. Tự đánh giá

Cùng nhóm hoàn thiện ba kiến trúc student, bảo vệ việc ghi refund ở host và so sánh các shape bằng dữ liệu benchmark. Kết quả public chọn workflow vì đạt 70/70 với chi phí mô phỏng thấp nhất. Giới hạn là chưa chạy hidden grader và MockLLM không đại diện cho model sản xuất.
