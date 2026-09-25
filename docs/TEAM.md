# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** `[Điền tên nhóm]`
- **Mã Nhóm / Lớp:** `K4-L3-DAY10`
- **Tên Repository Nộp Bài:** `K4-L3-DAY10-TenNhom-DataPipeline`

---

## # Thành viên

| STT | Họ và tên | MSSV | Email | Vai trò & Phân công công việc | Báo cáo cá nhân |
|---:|---|---|---|---|---|
| 1 | | | | Trưởng nhóm / Pipeline Integrator (`core/`, `phase1.py`, `corruption_flow.py`) | `report/<MSSV1>_HoTen.md` |
| 2 | Lê Đức Tùng | 2A202603005 | 26ai.tungld2@vinuni.edu.vn | Data Foundation & Recovery (`crossref.py`, `cleaning.py`, raw data) | `report/2A202603005_LeDucTung.md` |
| 3 | | | | RAG & Vector Index (`retrieval/index.py`, `embeddings.py`, ChromaDB) | `report/<MSSV3>_HoTen.md` |
| 4 | Nguyễn Công Vinh | 2A202602519 | | Observability & Evaluation (`quality.py` GX 1.x, `testset.py`, `reporting.py`) | `report/2A202602519_NguyenCongVinh.md` |

*(Nếu nhóm có 3 hoặc 5-6 thành viên, xem bảng phân công chi tiết theo vai trò trong file `CHECKPOINTS.md`)*.

---

## # Cá nhân

### ## HoVaTen1-MSSV1
- **Vai trò:** Trưởng nhóm & Điều phối Pipeline.
- **Công việc chi tiết đã hoàn thành:**
  - Thiết lập cấu hình hệ thống `core/config.py` và đường dẫn artifacts `core/utils.py`.
  - Kết nối luồng thực thi trong `src/pipelines/phase1.py` và `src/pipelines/corruption_flow.py`.
  - Kiểm tra tính nhất quán của các artifacts và theo dõi Contributor tracking trên GitHub nhánh `main`.
- **Điều học được / Đóng góp chính:**
  - Hiểu sâu sắc về thiết kế Idempotent Pipeline và quản lý trạng thái luồng dữ liệu đa tầng.

### ## HoVaTen2-MSSV2
- **Vai trò:** Phụ trách Ingestion, Làm sạch & Phục hồi dữ liệu.
- **Công việc chi tiết đã hoàn thành:**
  - Xây dựng module thu thập Crossref API với cơ chế Fallback offline trong `src/ingestion/crossref.py`.
  - Chuẩn hóa schema, tính toán trường `age_days` và `text_for_embedding` trong `src/ingestion/cleaning.py`.
  - Thực thi cơ chế Idempotent Repair phục hồi dữ liệu từ raw snapshot.
- **Điều học được / Đóng góp chính:**
  - Kỹ thuật truy vết nguồn gốc dữ liệu (Data Lineage) và bảo toàn raw snapshot trước khi biến đổi.

### ## HoVaTen3-MSSV3
- **Vai trò:** Phụ trách RAG, Vector Database & Embedding.
- **Công việc chi tiết đã hoàn thành:**
  - Quản lý mô hình embedding `sentence-transformers/all-MiniLM-L6-v2`.
  - Nạp và quản lý 3 collection riêng biệt trong ChromaDB (`papers-baseline`, `papers-corrupted`, `papers-repaired`).
  - Xây dựng QA Agent truy vấn ngữ cảnh chính xác theo tài liệu.
- **Điều học được / Đóng góp chính:**
  - Cách cô lập các không gian vector để so sánh khách quan giữa dữ liệu sạch và dữ liệu bị lỗi.

### ## Nguyễn Công Vinh - 2A202602519
- **Vai trò:** Phụ trách Data Observability & Benchmark Evaluation.
- **Công việc chi tiết đã hoàn thành:**
  - Xây dựng Quality Gate theo chuẩn **Great Expectations 1.x**, kiểm tra số lượng bản ghi, trường bắt buộc, tính duy nhất của `paper_id` và độ dài summary trong `src/observability/quality.py`.
  - Xây dựng kiểm tra Freshness SLA, thống kê số lượng và tỷ lệ bản ghi quá hạn, đồng thời xuất kết quả quality/freshness dạng JSON.
  - Hoàn thiện logic sinh benchmark trong `src/evaluation/testset.py` với các trường `id`, `question_type`, `question`, `ground_truth` và `ground_truth_doc_ids`.
  - Thiết kế lại `data/eval/test_set.json` gồm 10 câu hỏi dựa trên dữ liệu Crossref mới; phân bổ câu hỏi theo summary, authors và publication date do dữ liệu nguồn chưa có category.
  - Xây dựng `src/observability/reporting.py` để tổng hợp báo cáo baseline và bảng so sánh Baseline/Corrupted/Repaired khi pipeline cung cấp đủ kết quả đầu vào.
- **Điều học được / Đóng góp chính:**
  - Hiểu cách thiết lập Quality Gate và Freshness SLA để phát hiện sớm lỗi dữ liệu trước khi dữ liệu đi vào serving layer.
  - Hiểu cách xây dựng test set có ground truth bám sát dữ liệu thật và bảo đảm cùng một benchmark được dùng khi so sánh baseline, corrupted và repaired.
