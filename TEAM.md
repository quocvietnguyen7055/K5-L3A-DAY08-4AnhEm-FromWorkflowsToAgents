# Nhóm

## Thông tin nhóm

- Tên nhóm: 4AnhEm
- Lớp: L3A
- Repo nhóm: `K5-L3A-DAY08-4AnhEm-FromWorkflowsToAgents`
- URL repo: https://github.com/quocvietnguyen7055/K5-L3A-DAY08-4AnhEm-FromWorkflowsToAgents
- Nhánh nộp: `main`

## Thành viên

Danh tính được xác nhận trong GitHub issue #1. Nguyen Quoc Viet là nhóm trưởng. Vai trò chia theo bộ việc A–D (nhãn `A`–`D` của các GitHub issue). Email do từng thành viên tự cung cấp (issue #23, #24, nhánh `feat/Do-Duan`, báo cáo cá nhân).

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
| 1 | Nguyen Quoc Viet | 2A202603556 | rinthongminh@gmail.com | [quocvietnguyen7055](https://github.com/quocvietnguyen7055) | Nhóm trưởng; phần C: shape orchestrator và handoff |
| 2 | Le Quang Linh | 2A202603583 | linhlqhe181396@fpt.edu.vn | [linhlqhe181396](https://github.com/linhlqhe181396) | Phần B: shape single (ReAct) |
| 3 | Dau Phuc Duc | 2A202603580 | teflon125.work@gmail.com | [dpduc313](https://github.com/dpduc313) | Phần A: shape workflow, tích hợp, bonus B4 |
| 4 | Do Duc Duan | 2A202603590 | duandd1101@gmail.com | [Do-Duan](https://github.com/Do-Duan) | Phần D: ledger, crash và đánh giá |

## Bảng đóng góp

Mỗi dòng chỉ ghi commit có nội dung do chính người đó đứng tên trên nhánh `main`, không tính các commit merge PR. Riêng test của Le Quang Linh nằm trong commit merge `a62b4b8` của chính Linh. Đối chiếu: `git log --author=<tên> --stat main`.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Nguyen Quoc Viet (2A202603556) | Nhóm trưởng; phần C. Cài ba shape, sinh `benchmark.json` và `crash.json`, viết ADR, research card, báo cáo nhóm | `3614266` (ba shape, benchmark, crash), `c495637`, `4bec2f3`, `d669b6e` (báo cáo) | Chưa có (issue #13) |
| Le Quang Linh (2A202603583) | Phần B: test shape single | `a62b4b8` (test single), `ac2901f` (báo cáo cá nhân) | `src/tests/test_team_single.py` (2 test: C-002 seed 55 không tin ticket; giới hạn bước và `run_id` trong trace) |
| Dau Phuc Duc (2A202603580) | Phần A: test workflow, rà soát tái lập, ablation research card, tích hợp | `2307509` (test workflow), `7c40c0a` (ablation và research card), `541f382` (báo cáo cá nhân), `9bbf1a4` (email, vai trò), `00db032` (khôi phục file mẫu) | `src/tests/test_team_workflow.py` (33 test: T02 cả 5 seed theo order; trace và kết quả không lộ dữ liệu khách) |
| Do Duc Duan (2A202603590) | Phần D: demo durability và crash trong báo cáo nhóm, test quét lộ dữ liệu | `f39d8b4` (báo cáo nhóm, demo crash), `dd26bf9` (email, báo cáo cá nhân), `816ac9c` (test quét lộ dữ liệu) | `src/tests/test_team_leak_scan.py` (42 test: 3 shape × 14 claim public, trace, file `<run_id>*` và kết quả không chứa secret hay dữ liệu đơn hàng) |

## Báo cáo cá nhân

Báo cáo cá nhân của từng thành viên nằm tại:

- `report/team/2A202603556_NguyenQuocViet.md`
- `report/team/2A202603583_LeQuangLinh.md`
- `report/team/2A202603580_DauPhucDuc.md`
- `report/team/2A202603590_DoDucDuan.md`
