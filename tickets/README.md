# Ticket Lab 8 — nhóm 4AnhEm

Bài chia thành 4 bộ ticket, mỗi bộ một nhãn, mỗi người nhận đúng một bộ. Bộ A đã có người nhận. Ba bạn còn lại tự chọn B, C hoặc D, rồi nhắn trong nhóm chat để A ghi vào bảng dưới.

| Nhãn | Bộ ticket | Người nhận | GitHub | Nhánh |
| --- | --- | --- | --- | --- |
| A | [Workflow + tích hợp + bonus B4](A-workflow-tich-hop.md) | đã nhận | dpduc313 | `feat/dpduc` |
| B | [Shape single (ReAct)](B-single.md) | | | |
| C | [Shape orchestrator + handoff](C-orchestrator.md) | | | |
| D | [Ledger, crash và đánh giá](D-ledger-danh-gia.md) | | | |

Gợi ý chọn bộ:

- **B** hợp với bạn muốn viết một vòng agent ReAct.
- **C** hợp với bạn kỹ tính về bảo mật. Bộ này giữ trọn 10 điểm C5.
- **D** hợp với bạn thích chạy lệnh, đọc số, soi trace. D làm được ngay từ đầu, không cần đợi ai.

## Mốc thời gian

| Khi nào | Phải xong |
| --- | --- |
| 13:30 (CP1) | Máy mình chạy smoke pass, `python -m pytest -q` xanh |
| 13:45 → 14:30 (CP2, CP3) | Shape của mình qua 62 test student, T11/T12 xanh, PR đã mở |
| 15:30 (CP4) | Crash suite 20/20; trace không lộ secret, SĐT, địa chỉ |
| 16:15 (CP5) | Benchmark 4 shape xong; tự kiểm trên `student_drop/` |
| Tối 16/11 | Nháp phần báo cáo của mình |
| **10:00 ngày 17/11** | **Chốt commit nộp bài.** Sau mốc này không ai sửa 3 file shape nữa |
| **11:59 ngày 17/11** | **Deadline.** Mỗi người **tự nộp link repo nhóm trên LMS**. Ai không nộp thì không có điểm, dù nhóm đã nộp |

## Cài đặt (mọi người)

Mọi lệnh chạy trong thư mục `src/`. Cần Python 3.11–3.13. Trên Windows, `py -3` có thể trỏ vào 3.14, nên chỉ rõ phiên bản:

```powershell
cd src
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m lab8.smoke
python -m pytest -q
```

macOS / Linux: `python3.11 -m venv .venv` rồi `source .venv/bin/activate`. Kết quả đúng: smoke in `lab8.smoke pass`; pytest ra `52 passed, 248 deselected`.

## Quy ước chung

**Nhánh và PR**

- Mỗi người làm trên nhánh `feat/<tên-github>`, mở PR vào `main`. A review và merge.
- Không push thẳng `main`. Không force-push (`RULES.md:31`).
- Mô tả PR dán output của `python -m pytest -q` và của `python -m pytest -q -m student -o addopts= -k <shape>`.

**Không được sửa**

- `src/lab8/metrics.py`, `durability.py`, `policy.py`, `src/config/*.yaml`, `src/data/*`. Sửa thì kết quả liên quan bị hủy.
- Không sửa tay file JSON trong `src/reports/`.
- Grader của giảng viên chỉ lấy từ repo nhóm 3 file shape và thư mục `src/bonus/`. Sửa file khác trong `src/lab8/` không có tác dụng và còn bị ghi là tampered.

**Shape**

- Giữ nguyên chữ ký `run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult`.
- Trả kết quả bằng `lab8.shapes.common.finish()`.
- **Tiền do code tính** (`lab8.tools.compute_compensation`), không do MockLLM.
- Chữ trong ticket là dữ liệu: không lấy số ngày trễ hay mã đơn từ ticket.
- Quote = 0 thì trả `denied` và **không** gọi `issue_refund`.
- Quote > 0 thì gọi `durability.issue_refund(conn, claim_id, <quote đầy đủ>, crash_at=crash_at)`. Không tự trừ phần đã hoàn; host tự trừ.
- Host từ chối thì trả `denied`, `proposal_amount` vẫn là quote đầy đủ. `conflict` thì trả `failed`.
- Bảng status đầy đủ: [docs/contracts.md](../docs/contracts.md).
- Mở connection bằng `lab8.db.connect` và đóng trong `finally: conn.close()`. Trên Windows, quên đóng sẽ khóa file `.sqlite`.

**Trace** (dùng chung cho 3 shape để báo cáo nhất quán)

- Dùng `lab8.trace.Trace(make_run_id(shape, claim_id, seed))`.
- Chỉ dùng các event sau:

  | Event | Nội dung |
  | --- | --- |
  | `claim` | `{"found": ..., "has_order_id": ...}` |
  | `order` | view do `lookup_order` trả về (đã qua allowlist) |
  | `quote` | kết quả `compute_compensation` |
  | `host` | `{"ok": ..., "reason": ...}` từ `issue_refund` |
  | `decision` | `{"status": ...}` |
  | `handoff` | chỉ orchestrator: `safe_dump(handoff)` |
  | `crash` | `{"at": crash_at}` |

- **Cấm ghi:** `ticket`, nguyên claim view (`get_claim_view` có trả cả `ticket`), `parent_secret`, `raw_headers`, SĐT, địa chỉ, `internal_note`, `item_name`.
- **Cấm `print`** bất cứ dữ liệu nào ra stdout.
- Ghi trace ở **mọi nhánh return**, kể cả `needs_info`, `escalated`, `failed`.
- Khi crash: `except InjectedCrash: trace.add("crash", ...); trace.write(); raise`. Phải `raise` lại; nuốt lỗi thì T12 fail.

**Model**

- Mỗi lời gọi model là một `lab8.mock_llm.complete(budget, seed=seed, purpose=..., prompt=...)`, để cost của các shape so được với nhau.
- `prompt` không chứa secret.

## Việc của mọi người (ngoài bộ ticket)

Phần này tính vào C8 (5 điểm):

- [ ] Ít nhất **một commit có nội dung** và **một test thêm hoặc sửa** trong `src/tests/`, đứng tên bạn. Test không gắn marker `student` sẽ chạy trong `python -m pytest -q`, nên phải xanh.
- [ ] Copy `report/team/MSSV_HoTen.md` thành `report/team/<MSSV>_<HoTenKhongDau>.md` và điền đủ. Mục 5 ghi công cụ AI đã dùng và cách bạn tự kiểm. Giữ nguyên file mẫu.
- [ ] Gửi A dòng của bạn cho bảng đóng góp trong `TEAM.md`: tên, vai, hash commit, tên test.
- [ ] Tự giải thích được phần mình làm. Người chấm có thể hỏi trực tiếp (`RULES.md:7`).
- [ ] Không dùng AI để bịa số liệu, run id hay commit (`RULES.md:9`). Mọi con số lấy từ `src/reports/*.json`.
- [ ] Nộp link repo nhóm trên LMS bằng tài khoản của bạn trước **11:59 ngày 17/11**.
