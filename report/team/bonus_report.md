# Bonus report: B4

- **Topic và nguồn:** B4, baseline công bằng, ablation và thống kê. Nguồn: *Rethinking Evaluation of MAS Efficiency* (EMNLP 2026, slide 44, 59) và AgentArch (AACL 2026, slide 43).
- **CLAIM của nguồn:** "efficiency gain" của hệ đa tác tử có thể đến từ cách thiết kế benchmark; random pruning có lúc vẫn giữ được hiệu năng, nên phải so với single-agent và baseline đơn giản, giữ cố định runtime, model và tool.
- **BOUNDARY:** kết luận của nguồn rút ra trên các benchmark và mô hình ngôn ngữ thật mà nguồn đã thử. Nó không nói gì về một tác vụ hoàn tiền có luật nghiệp vụ cố định, chạy với MockLLM tất định.
- **HYPOTHESIS trên LogiX** (ghi trước khi chạy, trong phân tích ngày 16/11):
  - H1: trên bộ public, chênh lệch pass rate giữa workflow và swarm không có ý nghĩa thống kê.
  - H2: thêm một lời gọi model `draft` vào workflow không đổi pass rate, chỉ tăng chi phí.
  - H3: bỏ guard `needs_info` làm rơi claim thiếu `order_id`; bỏ guard quote = 0 có thể không làm rơi gì, vì host có cổng riêng.
  - H4: swarm bỏ ngẫu nhiên lời gọi `peer` và `parse` giữ được pass rate của swarm, với chi phí thấp hơn.
- **Biến cố định:** 14 claim public, seed 11/22/33/44/55, MockLLM, bảng giá, world, evaluator (`lab8.benchmark.run_benchmark`), một SQLite mới cho mỗi trial.
- **Biến thay đổi:** mỗi biến thể trong `src/bonus/` khác shape gốc đúng một thành phần:

| Biến thể | Gốc | Thay đổi duy nhất |
| --- | --- | --- |
| `workflow_draft` | workflow | thêm một `complete(purpose="draft")` ở mỗi nhánh kết thúc. Workflow gốc gọi model 0 lần, nên đây là ablation draft theo chiều thêm vào |
| `no_needs_info_guard` | workflow | bỏ bước dừng ở `needs_info` khi claim thiếu `order_id` |
| `no_zero_quote_guard` | workflow | bỏ bước dừng khi quote = 0, vẫn gửi quote 0 cho host |
| `swarm_pruned` | swarm | mỗi lời gọi `peer` và `parse` bị bỏ với xác suất 0.5, cố định theo SHA-256 của (seed, claim, purpose). Số ngày trong ticket chỉ có khi lời gọi `parse` được giữ |
| `swarm_no_override` | swarm | bỏ khối tin số ngày trong ticket (cùng ablation với research card) |

Baseline rules-only của B4 chính là `workflow`, vì shape này đã không gọi model lần nào. Chỗ thiếu duy nhất là thành phần investigator: không có biến thể nào chỉ thêm investigator vào workflow. Phép so workflow với orchestrator đổi nhiều thứ cùng lúc, nên chỉ dùng làm baseline, không coi là ablation.

- **Lệnh tái lập** (trong `src/`, chạy khoảng 1 phút): `python -m bonus.stats`. Lệnh này chạy benchmark 9 shape rồi tính thống kê. Chạy hai lần ra hai file giống nhau từng byte.
- **File report:** `src/reports/bonus_benchmark.json` (630 trial, cùng định dạng `lab8.benchmark`) và `src/reports/bonus_ablation.json` (CI, McNemar, safety counts). Các run id nêu trong báo cáo: `R-swarm-C-002-s55`, `R-swarm_pruned-C-002-s55`, `R-no_needs_info_guard-C-004-s11`.
- **Test:** `python -m pytest -q tests/test_bonus_b4.py` (11 test).

## Kết quả

CI95 dùng bootstrap theo claim: 2000 lần, seed 0, resample 14 claim cùng cả 5 seed của mỗi claim. Cột "Leak / bypass" đếm theo trial. Cả 630 trial đều bằng 0.

| Shape | Pass rate | CI95 theo claim | pass^5 | Phương sai seed | Cost/success (VND) | Model call | Tool call | Leak secret / PII / bypass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| workflow | 1.000 | [1.000, 1.000] | 1.000 | 0.000000 | 27.86 | 0.00 | 2.79 | 0 / 0 / 0 |
| single | 1.000 | [1.000, 1.000] | 1.000 | 0.000000 | 31.54 | 2.71 | 2.79 | 0 / 0 / 0 |
| orchestrator | 1.000 | [1.000, 1.000] | 1.000 | 0.000000 | 46.43 | 0.00 | 4.64 | 0 / 0 / 0 |
| swarm | 0.986 | [0.957, 1.000] | 0.929 | 0.000816 | 49.57 | 3.00 | 4.66 | 0 / 0 / 0 |
| workflow_draft | 1.000 | [1.000, 1.000] | 1.000 | 0.000000 | 28.87 | 1.00 | 2.79 | 0 / 0 / 0 |
| no_needs_info_guard | 0.929 | [0.786, 1.000] | 0.929 | 0.000000 | 30.77 | 0.00 | 2.86 | 0 / 0 / 0 |
| no_zero_quote_guard | 1.000 | [1.000, 1.000] | 1.000 | 0.000000 | 27.86 | 0.00 | 2.79 | 0 / 0 / 0 |
| swarm_pruned | 0.986 | [0.957, 1.000] | 0.929 | 0.000816 | 48.80 | 1.91 | 4.66 | 0 / 0 / 0 |
| swarm_no_override | 1.000 | [1.000, 1.000] | 1.000 | 0.000000 | 48.72 | 3.00 | 4.64 | 0 / 0 / 0 |

Bảng dưới dùng McNemar exact hai phía trên 70 cặp (claim, seed). A là đối chứng.

| Loại | A | B | B fail khi A đạt | B đạt khi A fail | p (McNemar exact) | Δ pass rate | Δ cost/success | Cặp bất đồng |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| baseline | workflow | swarm | 1 | 0 | 1.0000 | -0.014 | +21.71 | C-002/s55 |
| baseline | workflow | single | 0 | 0 | 1.0000 | +0.000 | +3.68 | - |
| baseline | workflow | orchestrator | 0 | 0 | 1.0000 | +0.000 | +18.57 | - |
| baseline | swarm | swarm_pruned | 0 | 0 | 1.0000 | +0.000 | -0.77 | - |
| ablation | workflow | workflow_draft | 0 | 0 | 1.0000 | +0.000 | +1.01 | - |
| ablation | workflow | no_needs_info_guard | 5 | 0 | 0.0625 | -0.071 | +2.91 | C-004/s11, C-004/s22, C-004/s33, C-004/s44, C-004/s55 |
| ablation | workflow | no_zero_quote_guard | 0 | 0 | 1.0000 | +0.000 | +0.00 | - |
| ablation | swarm | swarm_no_override | 0 | 1 | 1.0000 | +0.014 | -0.85 | C-002/s55 |

## Kết luận

**Chênh lệch giữa workflow và swarm không có ý nghĩa thống kê** (H1 được ủng hộ). Chỉ có một cặp bất đồng (C-002, seed 55), cho p = 1.0, và hai khoảng CI chồng lên nhau. Nhóm chọn workflow không phải vì pass rate cao hơn, mà vì ba lý do khác:

- **Cơ chế lỗi đã biết.** `swarm_no_override` bỏ đúng việc tin ticket thì lỗi biến mất.
- **Chi phí là số tất định.** Mỗi lần đạt, swarm tốn thêm 21.71 VND (+78%).
- **Quy tắc của đề.** Khi pass rate không phân biệt được, chọn shape ít tự chủ nhất.

**Thành phần bỏ đi hoặc thêm vào mà metric không đổi:**

- **Lời gọi `draft`** (H2 đúng). Pass rate giữ nguyên; chi phí mỗi lần đạt tăng 1.01 VND (+3.6%).
- **Guard quote = 0** (H3, nửa sau). Host tự từ chối với lý do `non_positive_amount`, nên điểm không đổi. Tuy vậy, mỗi claim C-002, C-006, C-009 có thêm một dòng audit `policy_denied` mà evaluator không đo. Trong vận hành thật, dòng đó là cảnh báo vi phạm chính sách giả. Vì vậy nhóm giữ guard này.
- **`peer` và `parse` khi bị bỏ ngẫu nhiên** (H4). Số lời gọi model giảm từ 3.00 xuống 1.91 mỗi claim mà pass rate giữ nguyên, khớp claim "random pruning vẫn giữ hiệu năng" của nguồn.

Ngoài ra còn hai điểm cần đọc kỹ:

- **Lỗi của `swarm_pruned` là do may rủi.** Ở C-002 seed 55, lời gọi `parse` tình cờ được giữ, nên lỗi tin ticket vẫn còn. Test `test_swarm_pruned_without_parse_cannot_trust_the_ticket` cho thấy nếu bỏ `parse` thì trial này đạt. Khả năng bỏ trúng là 0.5, nên đây chỉ là một lần rút ngẫu nhiên. Kỳ vọng của pass rate khi pruning là khoảng 0.993, không phải 0.986.
- **Guard `needs_info` tạo ra đúng 5 lượt đạt** (H3, nửa đầu): không có guard, C-004 trả `escalated` thay vì `needs_info` ở cả 5 seed. p = 0.0625 vẫn trên 0.05. Lý do không phải hiệu ứng yếu, mà là 5 cặp bất đồng cùng thuộc một claim, nên thực chất chỉ có một mẫu độc lập. Đây là ví dụ cho thấy p-value tính trên cặp (claim, seed) không thay được việc đọc cơ chế lỗi.

**Kết luận sẽ đảo ngược khi:**

- **Dữ liệu chỉ có trong câu chữ ticket**, không có order row. Khi đó lời gọi `parse` mang thông tin thật, và bỏ nó sẽ làm rơi pass rate.
- **Host không có cổng `non_positive_amount`.** Khi đó guard quote = 0 thành bắt buộc.
- **Bộ claim có thêm ca mà swarm sai do tin ticket ở nhiều claim khác nhau.** Khi đó McNemar mới có đủ cặp bất đồng độc lập để bác bỏ H1.

## Giới hạn

- **MockLLM tất định.** Model thật có thể làm `draft` hoặc `parse` có ích, hoặc có hại, theo cách bộ public không đo được. Chi phí là VND mô phỏng; không có latency (`latency: unavailable`).
- **Cỡ mẫu nhỏ và không độc lập.** Chỉ có 14 claim public, nên CI theo claim rất rộng: rơi một claim là cận dưới xuống 0.786. 5 seed của cùng một claim không độc lập, nên p-value tính theo cặp (claim, seed) lạc quan hơn thực tế.
- **Chưa kiểm trên hidden.** Chưa chạy bộ hidden 40 claim. Gate bonus (pass rate hidden ≥ 0.80) phụ thuộc grader của giảng viên.
- **Pruning chỉ rút một lần** với p = 0.5. Chưa chạy nhiều hạt giống pruning để lấy phân phối.
- **Đếm `approval_bypass` là đại diện gián tiếp**, suy từ trạng thái và lý do fail của evaluator (xem `bonus/stats.py`). Host vẫn là nơi chặn chính.
