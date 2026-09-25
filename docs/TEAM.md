# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** `P4P`
- **Mã Nhóm / Lớp:** `K4-L3-DAY10`
- **Tên Repository Nộp Bài:** `K4-L3-DAY10-P4P-DataPipeline`

---

# Thành viên

| STT | Họ và tên | MSSV | Email | Vai trò & Phân công công việc | Báo cáo cá nhân |
|---:|---|---|---|---|---|
| 1 | Nguyễn Văn Biển | 2A202602416 | nguyenbien5102005@gmail.com | Trưởng nhóm / Pipeline Integrator (`core/`, `phase1.py`, `corruption_flow.py`) | `report/2A202602416_NguyenVanBien.md` |
| 2 | Lê Đức Tùng | 2A202603005 | 26ai.tungld2@vinuni.edu.vn | Data Foundation & Recovery (`crossref.py`, `cleaning.py`, raw data) | `report/2A202603005_LeDucTung.md` |
| 3 | Huỳnh Tấn Trung | 2A202602742 | nghetrunghuynh@gmail.com| RAG & Vector Index (`retrieval/index.py`, `embeddings.py`, ChromaDB) | `report/2A202602742_HuynhTanTrung.md` |
| 4 | Nguyễn Công Vinh | 2A202602519 | 26ai.vinhnc@vinuni.edu.vn | Observability & Evaluation (`quality.py` GX 1.x, `testset.py`, `reporting.py`) | `report/2A202602519_NguyenCongVinh.md` |

*(Nếu nhóm có 3 hoặc 5-6 thành viên, xem bảng phân công chi tiết theo vai trò trong file `CHECKPOINTS.md`)*.

---

# Cá nhân

## NguyenVanBien-2A202602416
- **Vai trò:** Trưởng nhóm & Điều phối Pipeline.
- **Công việc chi tiết đã hoàn thành:**
  - Thiết lập cấu hình hệ thống `core/config.py` và đường dẫn artifacts `core/utils.py`.
  - Kết nối luồng thực thi trong `src/pipelines/phase1.py` và `src/pipelines/corruption_flow.py`.
  - Kiểm tra tính nhất quán của các artifacts và theo dõi Contributor tracking trên GitHub nhánh `main`.
  - Rà soát toàn repo theo Guide/Rubric: gộp nhánh Observability, chuẩn hóa `corruption.py` theo Guide, loại bỏ đường dẫn tuyệt đối khỏi manifest embeddings, khôi phục snapshot raw có `categories`.
- **Điều học được / Đóng góp chính:**
  - Hiểu sâu sắc về thiết kế Idempotent Pipeline và quản lý trạng thái luồng dữ liệu đa tầng.

## LeDucTung-2A202603005
- **Vai trò:** Phụ trách Ingestion, Làm sạch & Phục hồi dữ liệu.
- **Công việc chi tiết đã hoàn thành:**
  - Xây dựng module thu thập Crossref API (retry 429/5xx, fallback snapshot offline) trong `src/ingestion/crossref.py`.
  - Chuẩn hóa schema, tính `age_days`, khử trùng lặp theo `paper_id` và tạo `text_for_embedding` trong `src/ingestion/cleaning.py`.
  - Xây dựng 6 kịch bản làm bẩn dữ liệu có ghi log trong `src/ingestion/corruption.py` (`data/results/corruption_log.json`).
  - Cung cấp hàm cleaning dùng lại cho bước Idempotent Repair từ raw snapshot.
- **Điều học được / Đóng góp chính:**
  - Kỹ thuật truy vết nguồn gốc dữ liệu (Data Lineage) và bảo toàn raw snapshot trước khi biến đổi.

## HuynhTanTrung-2A202602742
- **Vai trò:** Phụ trách RAG, Vector Database & Embedding.
- **Công việc chi tiết đã hoàn thành:**
  - Phụ trách module `src/retrieval/` (embedding `all-MiniLM-L6-v2`, `index.py`, `qa.py`, `agent.py`, `llm.py`) và chuẩn hóa export trong `retrieval/__init__.py`.
  - Chạy pipeline để tạo 3 collection riêng biệt trong ChromaDB (`papers-baseline`, `papers-corrupted`, `papers-repaired`) và bộ artifact đầu tiên cho nhóm đối chiếu.
  - Xử lý xung đột khi gộp nhánh (commit `fix conflix`).
- **Điều học được / Đóng góp chính:**
  - Cách cô lập các không gian vector để so sánh khách quan giữa dữ liệu sạch và dữ liệu bị lỗi.

## NguyenCongVinh-2A202602519
- **Vai trò:** Phụ trách Data Observability & Benchmark Evaluation.
- **Công việc chi tiết đã hoàn thành:**
  - Xây dựng Quality Gate theo chuẩn **Great Expectations 1.x**, kiểm tra số lượng bản ghi, trường bắt buộc, tính duy nhất của `paper_id` và độ dài summary trong `src/observability/quality.py`.
  - Xây dựng kiểm tra Freshness SLA, thống kê số lượng và tỷ lệ bản ghi quá hạn, đồng thời xuất kết quả quality/freshness dạng JSON.
  - Hoàn thiện logic sinh benchmark trong `src/evaluation/testset.py` với các trường `id`, `question_type`, `question`, `ground_truth` và `ground_truth_doc_ids`.
  - Thiết kế `data/eval/test_set.json` gồm 10 câu hỏi (summary 3, authors 3, date 2, categories 2); logic tự động bỏ dạng `categories` và phân bổ lại sang các trường còn lại nếu dữ liệu nguồn không có category để không tạo ground truth giả.
  - Xây dựng `src/observability/reporting.py` để tổng hợp báo cáo baseline và bảng so sánh Baseline/Corrupted/Repaired khi pipeline cung cấp đủ kết quả đầu vào.
- **Điều học được / Đóng góp chính:**
  - Hiểu cách thiết lập Quality Gate và Freshness SLA để phát hiện sớm lỗi dữ liệu trước khi dữ liệu đi vào serving layer.
  - Hiểu cách xây dựng test set có ground truth bám sát dữ liệu thật và bảo đảm cùng một benchmark được dùng khi so sánh baseline, corrupted và repaired.
