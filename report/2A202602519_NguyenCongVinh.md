# BÁO CÁO CÁ NHÂN

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Nguyễn Công Vinh |
| MSSV | 2A202602519 |
| Khóa/Lớp | K4 |
| Nhóm | P4P |
| Vai trò chính | Observability & Evaluation |
| Repository | K4-L3-DAY10-P4P-DataPipeline |
| Ngày hoàn thành | 25/09/2026 |

## 2. Vai trò và phạm vi phụ trách

### 2.1. Phần việc phụ trách chính

| Hạng mục | File/Artifact liên quan | Trạng thái |
|---|---|---|
| Xây dựng kiểm tra chất lượng dữ liệu | `src/observability/quality.py` | Đã chạy: `success=true`, 6/6 expectations pass |
| Xây dựng báo cáo quan sát pipeline | `src/observability/reporting.py` | Hoàn thành phần code, chờ kiểm thử tích hợp |
| Xây dựng bộ sinh test set đánh giá | `src/evaluation/testset.py` | Đã chạy: sinh đủ 10 câu hỏi |
| Thiết kế bộ câu hỏi đánh giá theo dữ liệu mới | `data/eval/test_set.json` | Hoàn thành và đã xác minh |

### 2.2. Phần việc hỗ trợ nhóm

- Đối chiếu dữ liệu Crossref mới trong thư mục `data/raw` để cập nhật bộ câu hỏi đánh giá.
- Chuẩn hóa cấu trúc test set để phục vụ đánh giá retrieval và answer quality.
- Xác định các tiêu chí data quality, freshness và nội dung cần có trong báo cáo pipeline.

## 3. Kết quả theo vai trò

| Yêu cầu | Kết quả thực hiện | Minh chứng | Cách xác minh |
|---|---|---|---|
| Kiểm tra chất lượng dữ liệu | Xây dựng các kiểm tra số lượng bản ghi, trường bắt buộc, tính duy nhất của `paper_id` và độ dài summary | `data/quality/test_quality_report.json` | 24 dòng; `success=true`; 6/6 expectations pass |
| Kiểm tra độ mới dữ liệu | Tính ngày mới nhất, cũ nhất, số bản ghi quá hạn, tỷ lệ stale và trạng thái freshness | `src/observability/quality.py` | |
| Báo cáo baseline và corruption | Tạo nội dung báo cáo Markdown cho baseline và so sánh Baseline/Corrupted/Repaired | `src/observability/reporting.py` | |
| Bộ dữ liệu đánh giá | Tạo 10 câu hỏi với đáp án và DOI làm ground-truth document ID | `data/eval/test_set.json` | 10 câu hỏi, 10 DOI duy nhất |
| Sinh test set tái lập | Xây dựng logic chọn tài liệu và phân bổ loại câu hỏi có tính xác định | `src/evaluation/testset.py` | 4 summary, 3 authors, 3 date |

### Đầu ra cụ thể

- `quality.py` kiểm tra các ràng buộc chính của dữ liệu sạch bằng Great Expectations và tạo kết quả dạng JSON.
- `quality.py` đánh giá freshness theo ngưỡng thời gian và tỷ lệ bản ghi quá hạn được cấu hình.
- `reporting.py` tổng hợp trạng thái quality/freshness và các chỉ số đánh giá thành báo cáo Markdown.
- `testset.py` sinh câu hỏi theo các nhóm summary, authors, publication date và category khi dữ liệu hỗ trợ.
- `test_set.json` hiện chứa 10 câu hỏi gắn với 10 DOI duy nhất từ dữ liệu raw mới.

## 4. Giải thích kỹ thuật phần việc chính

### 4.1. Bài toán cần giải quyết

Pipeline cần có cơ chế phát hiện dữ liệu không đạt chất lượng, dữ liệu quá cũ và đo được ảnh hưởng của lỗi dữ liệu đến hệ thống RAG. Vì vậy, phần Observability & Evaluation phải cung cấp các kiểm tra có thể lặp lại, artifact rõ ràng và một test set có ground truth bám sát dữ liệu thật.

### 4.2. Cách tiếp cận

1. Kiểm tra các điều kiện nền tảng của dữ liệu: số dòng, trường bắt buộc, DOI duy nhất và nội dung đủ dài.
2. Tách freshness khỏi data quality để có thể xác định rõ lỗi về cấu trúc/nội dung và lỗi về thời gian.
3. Tạo báo cáo Markdown từ các artifact JSON thay vì ghi cứng kết quả.
4. Sinh test set có cấu trúc ổn định gồm `id`, `question_type`, `question`, `ground_truth` và `ground_truth_doc_ids`.
5. Khi metadata category không có trong dữ liệu mới, phân bổ lại câu hỏi sang summary, authors và date để không tạo ground truth giả.

### 4.3. Hợp đồng đầu vào và đầu ra

| Thành phần | Đầu vào | Đầu ra |
|---|---|---|
| Data quality | DataFrame dữ liệu sạch và settings | Kết quả kiểm tra và artifact JSON |
| Freshness | Cột ngày xuất bản và cấu hình ngưỡng | Thống kê stale/fresh và artifact JSON |
| Reporting | Kết quả quality, freshness và evaluation | Báo cáo Markdown |
| Test-set generator | Dữ liệu paper đã chuẩn hóa | Danh sách câu hỏi có ground truth |

### 4.4. Cách xác minh

```powershell
python -c "from core.config import load_settings; from observability.quality import run_data_quality_checks; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); res=run_data_quality_checks(df, s, 'test'); print('Tín hiệu hoàn thành: Quality check status =', res['success'])"

python -c "from core.config import load_settings; from evaluation.testset import build_test_set; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); ts=build_test_set(df, s.paths.eval_testset); print('Tín hiệu hoàn thành: Sinh được', len(ts), 'câu hỏi test')"
```

- Kết quả mong đợi: clean dataset có 24 dòng, Quality Gate trả `True` và test set có 10 câu hỏi.
- Kết quả thực tế: clean dataset có 24 dòng; Quality Gate `success=true` với 6/6 expectations pass; test set có 10 câu hỏi gắn với 10 DOI duy nhất.
- Artifact/log minh chứng: `data/clean/papers_clean.json`, `data/clean/papers_clean.csv`, `data/quality/test_quality_report.json`, `data/eval/test_set.json`.
- Trạng thái ChromaDB: chưa có collection `papers-baseline`; phần vector indexing của CP2 chưa đạt tín hiệu 24 documents.

## 5. Quyết định kỹ thuật quan trọng

### Quyết định: Không tạo câu hỏi category khi dữ liệu nguồn không có category

- **Bối cảnh:** 24 bản ghi Crossref mới không có giá trị trong `categories` và `primary_category`.
- **Các phương án đã cân nhắc:**
  - Tự suy luận category từ title hoặc summary.
  - Vẫn tạo câu hỏi category với đáp án rỗng.
  - Phân bổ số câu hỏi category sang các trường có ground truth đáng tin cậy.
- **Phương án được chọn:** Phân bổ bộ 10 câu thành 4 câu summary, 3 câu authors và 3 câu publication date.
- **Lý do:** Giữ test set bám sát dữ liệu thật, tránh tạo nhãn chủ đề không có căn cứ và bảo đảm kết quả đánh giá có thể tái lập.
- **Đánh đổi:** Chưa đánh giá được khả năng truy vấn theo category cho đến khi pipeline bổ sung metadata này.

## 6. Bug hoặc blocker đã gặp

### Blocker: Phần ChromaDB indexing của CP2 chưa hoàn thành

- **Hiện tượng:** `data/chroma/chroma.sqlite3` tồn tại nhưng ChromaDB chưa có collection; manifest `data/embeddings/papers_embeddings.json` cũng chưa được tạo.
- **Phạm vi ảnh hưởng:** Test set của CP2 đã đạt 10 câu nhưng CP2 chưa thể được đánh dấu hoàn thành và chưa thể chạy baseline evaluation.
- **Những gì đã kiểm tra:** Clean dataset có 24 dòng, Quality Gate pass và test set có 10 câu hỏi; truy vấn `list_collections()` trả danh sách rỗng.
- **Nguyên nhân hiện tại:** Bước build embedding/index chưa tạo thành công collection `papers-baseline`.
- **Bước tiếp theo:** Chạy `LocalEmbeddingIndex.build(...)`, xác minh `papers-baseline` có đúng 24 documents, sau đó mới chạy CP3.

## 7. Hiểu biết end-to-end về hệ thống

### 7.1. Dữ liệu đi từ Crossref đến Chroma như thế nào?

Dữ liệu được lấy từ Crossref và lưu dưới dạng raw JSON. Bước cleaning chuẩn hóa trường dữ liệu, loại bản ghi lỗi và tạo `text_for_embedding`. Sau đó hệ thống sinh embedding, lưu vector cùng metadata và document ID vào Chroma để phục vụ truy xuất.

### 7.2. Test set đánh giá retrieval và answer quality như thế nào?

Mỗi câu hỏi có `ground_truth_doc_ids` để kiểm tra tài liệu đúng có nằm trong kết quả truy xuất hay không. Trường `ground_truth` được dùng để so sánh nội dung câu trả lời bằng các metric như token F1 hoặc evaluator được cấu hình trong dự án.

### 7.3. Data quality và freshness khác nhau ở đâu?

Data quality kiểm tra cấu trúc và tính hợp lệ của dữ liệu như thiếu trường, trùng ID hoặc nội dung quá ngắn. Freshness kiểm tra dữ liệu có đủ mới theo thời gian hay không. Một bản ghi có thể đúng cấu trúc nhưng vẫn bị coi là stale.

### 7.4. Vì sao phải dùng cùng một test set cho baseline và corrupted?

Dùng cùng test set giúp kiểm soát biến số đầu vào. Khi đó chênh lệch metric phản ánh tác động của corruption hoặc repair, thay vì xuất phát từ việc thay đổi câu hỏi hay ground truth.

### 7.5. Khi nào có thể kết luận repair thành công?

Repair thành công khi các kiểm tra quality/freshness phục hồi, pipeline tạo đủ artifact và các metric của phiên bản repaired tiến gần hoặc đạt lại baseline trên cùng một test set.

## 8. Phân tích kết quả

| Metric | Baseline | Corrupted | Repaired | Nhận xét |
|---|---:|---:|---:|---|
| Retrieval | | | | |
| Answer quality | | | | |
| Data quality | Pass: 6/6 expectations, 24 dòng | | | CP1 đã được xác minh bằng artifact JSON |
| Freshness | | | | |

### Kết luận từ kết quả

- Dữ liệu sạch hiện đáp ứng toàn bộ 6 expectations đã cấu hình: đúng ngưỡng số dòng, không null ở ba trường bắt buộc, `paper_id` duy nhất và summary dài tối thiểu 30 ký tự.
- Test set đã sinh đủ 10 câu trên 10 DOI duy nhất. Do dữ liệu nguồn không có category, bộ câu hỏi thực tế gồm 4 summary, 3 authors và 3 date.
- Chưa có cơ sở kết luận về retrieval hoặc answer quality vì collection Chroma baseline chưa được tạo.

## 9. Bài học và hướng cải thiện

### Bài học rút ra

- Artifact và schema ổn định giúp các thành viên tích hợp các bước pipeline độc lập dễ hơn.
- Data quality và freshness cần được đo riêng để việc chẩn đoán lỗi rõ ràng.
- Test set phải được xây dựng từ dữ liệu thật; metadata thiếu sẽ ảnh hưởng trực tiếp đến phạm vi đánh giá RAG.

### Nếu có thêm thời gian

- Bổ sung hoặc làm giàu category từ nguồn đáng tin cậy ở bước ingestion/cleaning.
- Viết unit test cho quality checks, freshness checks, report rendering và test-set generation.
- Chạy đầy đủ baseline, corruption và repair để bổ sung số liệu cùng artifact vào báo cáo.

## 10. Cam kết cá nhân

- [x] Báo cáo phản ánh đúng phần việc đã thực hiện.
- [x] Tôi hiểu luồng xử lý end-to-end của hệ thống.
- [x] Các kết luận về CP1 và test set CP2 có số liệu hoặc artifact minh chứng.
- [x] Không khai báo CP2 hoặc kiểm thử end-to-end thành công khi Chroma indexing chưa hoàn tất.
- [x] Không đưa secret hoặc thông tin nhạy cảm vào báo cáo.
- [x] Nội dung không sao chép báo cáo của thành viên khác.

**Người thực hiện:** Nguyễn Công Vinh

**MSSV:** 2A202602519

**Ngày:** 25/09/2026
