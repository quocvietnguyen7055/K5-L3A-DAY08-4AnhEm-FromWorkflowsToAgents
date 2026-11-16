# Biên bản quyết định kiến trúc

- Shape chọn: workflow
- Commit hash: f2d83b9 (đủ shape, test, bonus và `src/reports/*.json`; ba shape và `benchmark.json`, `crash.json` không đổi từ `3614266`)
- Run id dẫn chứng: R-workflow-C-001-s11
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000–1.000 / 0.000000 (`reports/benchmark.json`, 70 lượt chạy)
- Cost per success (mô phỏng, VND): 27.86
- Crash safety: 20/20 (`src/reports/crash.json`)
- Secret leak / approval bypass: 0 / 0 trên 70 lượt public của workflow (`src/reports/bonus_ablation.json`, mục `by_shape.workflow.safety`; cũng bằng 0 ở cả 9 shape, 630 lượt). Test `tests/test_team_leak_scan.py` quét trace và kết quả của 3 shape × 14 claim. Chưa chạy bộ chấm hidden.

## Vì sao chọn kiến trúc này

Chọn workflow cho nhóm yêu cầu hoàn phí này vì workflow đạt 70/70 lượt, pass^5 = 1.000 và chi phí mô phỏng mỗi lần thành công thấp nhất (27.86 VND). Single và orchestrator cũng đạt 70/70 nhưng lần lượt tốn 31.54 và 46.43 VND mỗi lần thành công. Swarm đạt 69/70, pass^5 = 0.929, phương sai = 0.000816 và tốn 49.57 VND mỗi lần thành công. Kết quả dùng chung 14 yêu cầu, 5 seed, MockLLM, giá công cụ và bộ đánh giá. Đây là bằng chứng trong bộ dữ liệu lab, không phải kết luận cho mọi tác vụ.

## Có nên đổi sang nhiều tác tử không?

Trong bộ dữ liệu này, orchestrator không cải thiện tỷ lệ đạt so với workflow và tốn thêm khoảng 66.7% cho mỗi lần thành công. Swarm có thêm một lỗi ở C-002, seed 55: tin số ngày trong phiếu thay vì dữ liệu đơn hàng. Chênh lệch 70/70 so với 69/70 không có ý nghĩa thống kê (McNemar exact p = 1.0, `report/team/bonus_report.md`), nên nhóm không dựa vào nó. Lý do chọn là cơ chế lỗi: bỏ đúng khối tin phiếu (`swarm_no_override`) thì swarm đạt 70/70 mà vẫn đắt hơn workflow 20.86 VND mỗi lần đạt. Chỉ nên cân nhắc nhiều tác tử khi công việc có các phần độc lập và investigator cải thiện độ chính xác đủ bù chi phí; cần kiểm chứng trên bộ dữ liệu đại diện mới.

## Trace và bằng chứng

Trace chỉ ghi các trường đã cho phép như mã yêu cầu/đơn hàng, trường đơn hàng, báo giá, handoff đã lọc và quyết định. Trace không ghi nguyên văn phiếu, mã khách hàng, header thô, bí mật cha, địa chỉ, số điện thoại hoặc ghi chú nội bộ. Handoff được tạo bằng `make_handoff`; investigator chỉ có công cụ đọc. Bằng chứng hiện có gồm bộ kiểm tra host/public và crash. Không có bộ hidden trong workspace nên chưa thể kết luận về bộ đó.

## Giới hạn

MockLLM không đại diện cho mô hình sản xuất; chi phí là số mô phỏng bằng VND và không đo độ trễ. Benchmark public chỉ có 14 yêu cầu × 5 seed. Chưa chạy tự kiểm tra hidden. Đóng góp chung được ghi trong `TEAM.md` và bốn báo cáo cá nhân.
