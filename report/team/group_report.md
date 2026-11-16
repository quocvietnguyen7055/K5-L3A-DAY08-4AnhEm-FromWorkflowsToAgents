# Báo cáo nhóm — Lab 8 LogiX-VN

## 1. Thông tin nhóm

- Tên nhóm: 4AnhEm
- Thành viên: bốn thành viên ghi trong `TEAM.md`; GitHub issue #1 đã đóng sau khi ghi nhận danh tính.
- Commit mã nguồn và bằng chứng benchmark: `3614266`; nội dung báo cáo được cập nhật trong các commit tiếp theo.

## 2. Mục tiêu và cách tiếp cận

So sánh workflow, tác tử đơn ReAct, orchestrator và swarm trên cùng yêu cầu, seed, dữ liệu thế giới, chính sách giá và bộ đánh giá. Mã host quyết định số tiền, approval, quyền sở hữu, giới hạn hoàn tiền theo đơn, tính lặp an toàn và ghi sổ. Shape không tự ghi refund; phải gửi đầy đủ báo giá để host áp dụng giới hạn.

## 3. Giải pháp

- **Workflow:** đọc phần claim view được phép, tra đơn theo chủ thể, tính báo giá từ dữ liệu đơn và chính sách hiện hành, rồi gọi host. Không dùng nội dung phiếu để tính tiền.
- **Single:** chạy vòng ReAct tối đa 8 bước với công cụ chỉ đọc; model không có công cụ ghi. Báo giá lấy từ công cụ tính trong mã, sau đó shape gọi host.
- **Orchestrator:** tạo handoff theo allowlist, chỉ cấp công cụ đọc cho investigator và chỉ ghi handoff đã lọc vào trace; orchestrator chuyển báo giá cho host.
- **Swarm:** shape tham chiếu để đối chứng. Với seed chia hết cho 5, shape này cố ý tin số ngày ghi trong phiếu; điểm yếu xuất hiện ở C-002, seed 55.

Trace không chứa nguyên văn phiếu, mã chủ thể, thông tin liên hệ, ghi chú nội bộ, header thô hoặc canary secret. Handoff chỉ chứa tác vụ, mã yêu cầu/claim, facts được allowlist và tên công cụ đọc.

## 4. Kết quả

Nguồn số liệu: `src/reports/benchmark.json` (14 yêu cầu × 5 seed, 70 lượt/shape) và `src/reports/crash.json`.

| Kiến trúc | Tỷ lệ đạt | Pass^5 | Seed thấp–cao | Phương sai | Chi phí/lần đạt (VND mô phỏng) | Bước trung bình / p95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Workflow | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 27.86 | 2.86 / 3 |
| Single | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 31.54 | 2.79 / 3 |
| Orchestrator | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 46.43 | 3.71 / 4 |
| Swarm | 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 2.80 / 3 |

Bộ kiểm tra crash đạt 20/20. Cổng kiểm tra host (`python -m pytest -q`): 142 đạt, gồm test của nhóm và 11 test bonus. Ma trận student: 248 đạt. Bộ kiểm tra hồ sơ báo 0 lỗi, 0 cảnh báo. Chọn workflow vì tỷ lệ đạt tương đương các shape khác nhưng chi phí thấp nhất trên bộ dữ liệu này. Xem chi tiết và giới hạn trong `decision_adr.md`; phép so sánh kiến trúc ở `research_card.md`.

Bonus B4 (`bonus_report.md`, lệnh `python -m bonus.stats`) kiểm lại kết luận trên bằng thống kê và ablation:
- Chênh lệch workflow–swarm không có ý nghĩa thống kê (McNemar exact p = 1.0).
- Thêm một lời gọi model `draft` vào workflow không thêm lượt đạt nào, chỉ tốn thêm 1.01 VND mỗi lần đạt.
- Bỏ guard `needs_info` làm rơi C-004 ở cả 5 seed.
- Bỏ guard quote = 0 thì điểm không đổi, vì host tự từ chối, nhưng log có thêm dòng audit `policy_denied` giả.

## 5. Khó khăn và cách xử lý

Ba shape ban đầu là stub. Đã triển khai theo contract, chuyển tiếp điểm crash vào durability và giữ host làm nơi duy nhất ghi refund. Kết quả được kiểm tra bằng cổng host, toàn bộ ma trận student, benchmark và crash suite. Trace không ghi nguyên văn nội dung phiếu.

Thử nghiệm `python -m lab8.demo.buggy_workflow` in `unsafe refund rows: 2`, minh họa checkpoint riêng lẻ không bảo đảm ghi tiền đúng một lần: nếu tiến trình dừng sau khi tạo refund nhưng trước khi lưu checkpoint, lần chạy lại có thể tạo refund thứ hai. Với swarm trên cùng DB `data/crash.sqlite`, claim `C-012`, seed `11`, chạy lần đầu với `--crash-at after_effect_before_checkpoint` báo crash sau effect; khi đó ledger có 1 refund và 1 audit `refund_committed`. Chạy lại bỏ `--crash-at` trả `resolved`; tổng vẫn là 1 refund và 1 audit. Ledger/idempotency key `refund:C-012` giúp lần resume nhận ra effect đã có.

Ba điểm crash cần phân biệt: `before_effect` xảy ra trước khi ghi refund nên resume có thể ghi một effect; `after_effect_before_checkpoint` xảy ra sau effect nhưng trước checkpoint nên resume phải tránh ghi trùng; `after_checkpoint` xảy ra sau khi cả effect và checkpoint đã lưu nên resume cũng không được tạo effect mới. Cặp chạy trên xác nhận trực tiếp điểm giữa; kết quả toàn bộ các điểm được kiểm tra bằng crash suite 20/20.

Một phát hiện về đề: `docs/bonus_topics.md` có bảy topic B1–B7, nhưng `python -m lab8.check_submission` chỉ chấp nhận tiêu đề `Bonus report: B1` đến `B6`, nên báo FAIL nếu nhóm chọn B7. Nhóm chọn B4 nên không bị ảnh hưởng.

## 6. Tổng hợp đóng góp

Việc được chia theo bốn bộ A–D (nhãn GitHub issue). Nguyen Quoc Viet (nhóm trưởng, phần C) cài ba shape, sinh benchmark và crash, viết khung ADR và báo cáo. Le Quang Linh (phần B) viết test cho single. Dau Phuc Duc (phần A) viết test workflow, rà soát tái lập, ablation trong research card và bonus B4. Do Duc Duan (phần D) viết đoạn demo durability và test quét lộ dữ liệu. Commit và test của từng người ghi trong bảng đóng góp của `TEAM.md`, đối chiếu được bằng `git log`.

## 7. Hạn chế và hướng cải thiện

MockLLM không đại diện cho mô hình sản xuất; giá là mô phỏng bằng VND và không có số đo độ trễ. Bộ dữ liệu public chỉ có 14 yêu cầu và 5 seed; chưa chạy hidden grader/tự kiểm tra hidden. Bảng ở mục 4 so các triển khai đầy đủ. Các ablation một biến trong `research_card.md` và `bonus_report.md` đã tách được một phần: lỗi duy nhất của swarm đến từ việc tin số ngày trong phiếu, không phải từ topology. Phần chi phí còn lại là giá của topology (peer, parse, investigator, draft). Riêng investigator thì chưa có biến thể nào chỉ thêm đúng thành phần này vào workflow, nên ảnh hưởng của nó chưa được tách riêng.

Ở single, nếu vòng ReAct dừng vì chạm giới hạn 8 bước (`step_cap`) hoặc gặp công cụ lạ, kết quả rơi vào `denied` thay vì `failed`. Với hàm `decide` hiện tại, trường hợp này không xảy ra (mỗi claim chỉ tốn tối đa 3 bước), nên nhóm giữ nguyên và ghi lại ở đây. Cần kiểm tra thêm trên dữ liệu đại diện và xác nhận kết quả hidden trước khi khái quát kết luận.

## 8. Tài liệu tham khảo

- Bogavelli, T., Subramani, H. và Sharma, R. (2026). *AgentArch: A Benchmark for Evaluating Agent Architectures in Enterprise Workflows*. AACL-IJCNLP 2026. https://aclanthology.org/2026.aacl-long.44/
