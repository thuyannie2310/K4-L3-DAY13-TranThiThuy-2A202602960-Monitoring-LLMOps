# Chạy bài đã hoàn thiện ở máy này

## 1. Chạy local, không cần tài khoản

Mở terminal tại thư mục repository:

```bash
source .lab-venv/bin/activate
python -m pytest -q
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Mở terminal thứ hai, kích hoạt cùng môi trường rồi chạy:

```bash
python scripts/load_test.py --concurrency 5
python scripts/validate_logs.py
python scripts/validate_dashboard.py
python scripts/build_dashboard.py
open submission/evidence/11-dashboard.html
```

Lệnh build_dashboard tạo snapshot; chạy lại khi có dữ liệu mới. Ảnh chụp dashboard
này có thể lưu vào submission/evidence/11-dashboard-overview.png.

Trên máy khác, dùng Python 3.13 tạo `.venv` và cài requirements theo README.
Không sao chép `.lab-venv` giữa các máy.

## 2. Langfuse là gì và cần làm gì?

Langfuse là nơi xem timeline các bước xử lý một yêu cầu AI và lưu phiên bản
prompt. Chạy local chưa cấu hình key vẫn dùng được API, nhưng không có cloud trace.

1. Truy cập Langfuse Cloud theo link trong README, đăng ký hoặc đăng nhập.
2. Tạo project cá nhân `day13-k4-l3a-2A202602960`.
3. Trong project, tạo API key pair theo docs/SETUP.md.
4. Copy `.env.example` thành `.env`. Điền public key và secret key **trong file
   trên máy**, không gửi qua chat hoặc đưa vào Git. Base URL phải đúng region
   của project.
5. Tạo text prompt `day13-chat`, nội dung:

```text
Feature={{feature}}
Docs={{docs}}
Question={{message}}
```

6. Gắn label baseline và production cho v1. Tạo v2 thêm yêu cầu trả lời ngắn,
   giữ nguyên ba biến, gắn candidate. Xem docs/PROMPT_VERSIONING.md.
7. Dừng API bằng Ctrl+C rồi chạy lại:

```bash
uvicorn app.main:app --env-file .env
```

8. Chạy load_test để tạo 10 requests, chờ export rồi kiểm tra trace list trên
   project của mình. Mở trace để xem root → retrieval/generation.
9. Chạy workload lần lượt với baseline, candidate và production sau promote;
   đổi production về v1 rồi chạy lại. Khởi động lại API sau mỗi thay đổi label
   để tránh cache prompt. Lưu trace IDs và ảnh, không chụp màn hình API Keys.

Một trace là một lần thực thi; span/observation là một bước bên trong.
Correlation ID giống mã phiếu tra cứu, nối request trong log với trace tương ứng.

## 3. Challenge là gì?

Challenge là file giảng viên gửi riêng để tái hiện sự cố chấm điểm. Khi chưa nhận
thì không tự tạo. Có thể luyện tập bằng:

```bash
python scripts/inject_incident.py --scenario rag_slow
python scripts/load_test.py --concurrency 5
python scripts/build_dashboard.py
python scripts/inject_incident.py --scenario rag_slow --disable
```

Sau khi có file chính thức, xem docs/CHECKPOINTS.md CP3. Không commit challenge.json.

## 4. Đọc kết quả

- 100/100 log validator: đạt kiểm tra schema/context/PII của validator, không phải
  tổng điểm bài lab.
- 6/6 dashboard validator: contract đúng, vẫn cần ảnh dashboard runtime.
- Tests pass: phần mã được kiểm thử đạt; không chứng minh trace đã lên cloud.
- Báo cáo hiện là bản nháp kỹ thuật, còn các ô việc phải hoàn thành trước khi nộp.

## 5. Dashboard live và tái hiện ảnh evidence

```bash
python scripts/build_dashboard.py --serve
# Mở http://127.0.0.1:8765; logs được đọc lại mỗi 30 giây.
```

Để tái hiện đúng số liệu trong báo cáo, không phụ thuộc giờ hiện tại:

```bash
python scripts/build_dashboard.py --logs submission/evidence/04-structured-logs.jsonl --end 2026-09-29T07:41:06.932387+00:00
```

Bản evidence cố định không tự refresh. File JSON đi kèm lưu đủ số liệu và time range.
