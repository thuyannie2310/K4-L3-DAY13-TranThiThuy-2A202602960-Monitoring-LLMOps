# Runbook vận hành

Các biểu thức trong config là đặc tả; chưa kết nối alert engine/Slack thật.
Owner: TranThiThuy. Kênh dự kiến: `#llmops-alerts`. Không có request thì
SLI là N/A; không coi thiếu dữ liệu là hệ thống khỏe. Kiểm tra traffic riêng.

## Alert 1

`high_tail_latency`, warning: P95 trong cửa sổ 5 phút > 3000 ms liên tục
5 phút, tối thiểu 20 request. Người dùng chờ lâu; tiêu hao SLO 99.5%.

1. Xem latency/TTFT và traffic cùng khoảng UTC; so sánh baseline.
2. Lọc response_sent có latency_ms > 3000, lấy correlation_id.
3. Mở trace cùng ID, so sánh retrieval và generation, xem version prompt.

Mitigation: rollback thay đổi liên quan; giới hạn concurrency, đặt timeout hoặc
fallback retrieval nếu dependency chậm. Trong practice tắt `rag_slow` và chạy
lại cùng workload. Xác nhận P95 phục hồi, error không tăng trong 10 phút.

## Alert 2

`high_request_error_rate`, critical: tỷ lệ request_failed/request_received > 2%
trong 5 phút, duy trì 5 phút, ít nhất 20 request. Người dùng không nhận câu trả lời.

1. Xem error rate, error_type và retrieval success trên dashboard.
2. Tìm request_failed trong đúng khoảng; lấy correlation_id và error_type.
3. Mở trace tương ứng để xác nhận observation lỗi và dependency bị ảnh hưởng.

Mitigation: rollback deployment/prompt nếu có tương quan; fallback hoặc circuit
breaker dependency lỗi, retry có giới hạn cho lỗi tạm thời. Trong practice tắt
`tool_fail`. Xác nhận error < 2%, retrieval >= 90% trong 10 phút.

## Alert 3

`low_answer_quality`, warning: quality trung bình 15 phút < 0.75 duy trì 15 phút,
ít nhất 20 response. Đây chỉ là heuristic, cần review câu trả lời trước kết luận.

1. So sánh quality với baseline, prompt version, token và cost cùng cửa sổ.
2. Lấy correlation_id của response có quality thấp; kiểm tra preview đã scrub.
3. Mở trace, xem retrieval và prompt/version; chạy lại tập câu hỏi cố định.

Mitigation: rollback production về prompt đã kiểm chứng; kiểm tra corpus và
retrieval fallback. Review thủ công tập đánh giá; chỉ promote khi chất lượng
phục hồi >= 0.75 và latency/cost không vượt guardrails.
