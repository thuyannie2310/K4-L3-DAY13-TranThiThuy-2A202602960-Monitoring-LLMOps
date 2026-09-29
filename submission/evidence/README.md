# Evidence của bài lab cá nhân

Xem bảng evidence và diễn giải tại [REPORT.md](../REPORT.md).

- 00-*: baseline trước sửa; 01/02/03: kiểm tra mới nhất trên working tree (29 tests, log 100/100, dashboard 6/6).
- 04-structured-logs.jsonl: 84 dòng log practice; nguồn của dashboard 40 requests.
- 04-structured-log.png và 05-pii-redaction.png: ảnh hiển thị nguyên giá trị log runtime ở 05-pii-runtime.jsonl; HTML đi kèm chỉ phục vụ trình bày.
- 05-pii-checks.json: header/correlation ID và xác minh bốn loại PII giả.
- 11-dashboard*: cửa sổ practice cố định, có sáu panel và ngưỡng đúng từng chỉ số.
- 12-cloud-observations.json: 42 observations / 14 traces đọc lại từ Langfuse; bỏ metadata SDK chứa public key.
- 12-prompt-runs.json: baseline/candidate/promote/rollback cùng input.
- 13/14: ảnh prompt trước/sau rollback; 15/16: trace list và timeline/metadata.
- 17-langfuse-validation.txt: kết quả lần kết nối Langfuse trước đó (27 tests tại thời điểm đó).
- 18-evidence-audit.txt: kiểm tra evidence/secret/link mới nhất.

Chưa có incident challenge chính thức. Không dùng practice thay thế challenge và không commit config/challenge.json.
