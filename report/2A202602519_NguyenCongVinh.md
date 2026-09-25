# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Nguyễn Công Vinh           |
| MSSV               | 2A202602519                |
| Khóa/Lớp         | K4                         |
| Tên nhóm         | P4P                        |
| Vai trò chính    | Observability & Evaluation |
| Repository         | https://github.com/nguyenbien8/K4-L3-DAY10-P4P-DataPipeline |
| Ngày hoàn thành | 2026-09-25                 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Quality Gate GX 1.x | `src/observability/quality.py::run_data_quality_checks` | DataFrame + settings | `data/quality/{baseline,corrupted,repaired}_quality_report.json` | Hoàn thành |
| Freshness SLA | `src/observability/quality.py::build_freshness_report` | Cột `age_days`/`published` | `data/quality/*freshness_report.json` | Hoàn thành |
| Test set benchmark | `src/evaluation/testset.py::build_test_set` | DataFrame sạch | `data/eval/test_set.json` (10 câu) | Hoàn thành |
| Báo cáo Markdown | `src/observability/reporting.py` | metrics, quality, freshness | `data/reports/phase1_report.md`, `corruption_report.md` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Đối chiếu dữ liệu Crossref trong `data/raw` để thiết kế câu hỏi | Lê Đức Tùng | Câu hỏi bám đúng trường có trong dữ liệu |
| Thống nhất khóa `question_type`, `ground_truth_doc_ids` với `evaluation/metrics.py` | Nguyễn Văn Biển, Huỳnh Tấn Trung | `evaluate_pipeline` đọc test set không lỗi |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| 4 expectations GX 1.x | `quality.py` | Baseline PASS 6/6 kiểm tra, corrupted FAIL | `baseline_quality_report.json`, `corrupted_quality_report.json` |
| Freshness SLA | `quality.py` | Baseline FRESH, corrupted STALE | `freshness_report.json`, `corrupted_freshness_report.json` |
| Test set 10 câu | `testset.py` | summary 3, authors 3, date 2, categories 2 | Guide Bước 5: `Sinh được 10 câu hỏi test` |
| Báo cáo tự động | `reporting.py` | Bảng 3 trạng thái + phân tích tính từ số liệu | `data/reports/corruption_report.md` |

Output cụ thể: trên dữ liệu corrupted, Quality Gate phát hiện 2 vi phạm (`expect_column_values_to_be_unique` trên `paper_id`, `expect_column_value_lengths_to_be_between` trên `summary`) và freshness báo STALE với tỷ lệ bài cũ 0.318.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Pipeline cần cơ chế phát hiện dữ liệu không đạt chất lượng hoặc quá cũ trước khi vào vector store, và cần đo được ảnh hưởng của lỗi dữ liệu tới RAG bằng một test set có ground truth ổn định.

### Cách triển khai

1. **GX 1.x đúng chuẩn:** `gx.get_context(mode="ephemeral")` → `data_sources.add_pandas` → `add_dataframe_asset` → `add_batch_definition_whole_dataframe` → `get_batch(batch_parameters={"dataframe": df})`, không dùng cú pháp cũ `context.sources.pandas_default`.
2. **4 expectations:** `ExpectTableRowCountToBeBetween(5, 5000)`; `ExpectColumnValuesToNotBeNull` cho `paper_id`, `title`, `text_for_embedding`; `ExpectColumnValuesToBeUnique("paper_id")`; `ExpectColumnValueLengthsToBeBetween("summary", min_value=30)`. Mỗi expectation được validate riêng; nếu thiếu cột thì ghi thành check FAIL thay vì làm sập pipeline.
3. **Freshness tách riêng quality:** đếm dòng có `age_days > 180`, `is_fresh = stale_ratio ≤ 0.25`; ghi thêm ngày mới nhất/cũ nhất.
4. **Test set xác định:** chọn tài liệu theo thứ tự cố định, mỗi câu một DOI khác nhau, dùng mẫu câu mà `qa.py` nhận ra (tên bài trong dấu nháy đơn). Nếu dữ liệu không có category thì tự phân bổ sang summary/authors/date để không tạo ground truth giả.
5. **Báo cáo từ artifact:** mọi con số trong Markdown lấy từ payload JSON thật, không ghi cứng.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | DataFrame sạch/bẩn/repaired (cột `paper_id`, `title`, `summary`, `text_for_embedding`, `age_days`, `published`), `Settings` |
| Output | Quality report `{report_name, success, row_count, expectations[]}`; freshness `{latest_published, oldest_published, stale_rows, total_rows, stale_ratio, is_fresh}`; test set `[{id, question_type, question, ground_truth, ground_truth_doc_ids}]` |
| Module phụ thuộc | `ingestion/cleaning.py` (schema), `core/config.py` (đường dẫn, ngưỡng 180 ngày) |
| Module sử dụng output | `pipelines/phase1.py`, `pipelines/corruption_flow.py`, `evaluation/metrics.py` |
| Điều kiện lỗi cần xử lý | Thiếu cột; DataFrame rỗng; không đủ tài liệu cho một dạng câu hỏi; không có category |

### Cách xác minh

```bash
python -c "from core.config import load_settings; from observability.quality import run_data_quality_checks; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); res=run_data_quality_checks(df, s, 'test'); print(f'Tín hiệu hoàn thành: Quality check status = {res[\"success\"]}')"
python -c "from core.config import load_settings; from evaluation.testset import build_test_set; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); ts=build_test_set(df, s.paths.eval_testset); print(f'Tín hiệu hoàn thành: Sinh được {len(ts)} câu hỏi test')"
```

- **Kết quả mong đợi:** `Quality check status = True`, `Sinh được 10 câu hỏi test`.
- **Kết quả thực tế:** `Quality check status = True`, `Sinh được 10 câu hỏi test`.
- **Artifact/log:** `data/quality/baseline_quality_report.json`, `data/eval/test_set.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Có lúc dữ liệu Crossref tải live không có trường category, trong khi đề yêu cầu câu hỏi `categories`.
- **Các phương án đã cân nhắc:** (a) tự suy luận category từ title/summary; (b) vẫn tạo câu hỏi category với đáp án rỗng; (c) phân bổ số câu category sang các trường có ground truth đáng tin cậy.
- **Phương án đã chọn:** (c) làm cơ chế dự phòng trong code; khi dữ liệu có category (snapshot hiện tại) thì dùng đủ 4 dạng 3/3/2/2.
- **Lý do:** Không tạo nhãn không có căn cứ; test set luôn bám dữ liệu thật và tái lập được.
- **Bằng chứng quyết định phù hợp:** với snapshot hiện tại, test set có đủ 4 dạng; baseline `retrieval_hit_rate` = 1.000.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Khi kiểm tra CP2, `data/chroma/chroma.sqlite3` tồn tại nhưng `list_collections()` trả danh sách rỗng; chưa có manifest `data/embeddings/papers_embeddings.json`.
- **Lệnh hoặc bước tái hiện:** Chạy test set xong rồi truy vấn ChromaDB trước khi pipeline tích hợp được chạy.
- **Nguyên nhân gốc:** Bước build index chưa được gọi; ngoài ra nhánh `vinh/Observability-Evaluation` chưa được merge vào `main`, nên `main` vẫn dùng bản kiểm tra bằng pandas thay vì GX 1.x.
- **Cách xử lý:** Nguyễn Văn Biển merge nhánh vào `main` và chạy `run_phase1.py`, tạo collection `papers-baseline`.
- **Cách xác minh sau khi sửa:** `papers-baseline` 24 docs, `papers-corrupted` 22 docs, `papers-repaired` 24 docs.
- **Điều học được:** Tín hiệu hoàn thành của một checkpoint phải kiểm trên nhánh `main`, không chỉ trên nhánh cá nhân.

## 7. Hiểu biết về luồng end-to-end

1. **Crossref → Chroma:** raw JSON được parse và lưu; cleaning chuẩn hóa trường và tạo `text_for_embedding`; Quality Gate kiểm tra; embedding MiniLM cùng metadata và document ID được nạp vào Chroma.
2. **Evaluation set:** `ground_truth_doc_ids` dùng để kiểm tra tài liệu đúng có trong top-4 kết quả hay không (Hit Rate); `ground_truth` dùng cho Token F1 và LLM Judge.
3. **Quality vs freshness:** quality kiểm tra cấu trúc và tính hợp lệ (thiếu trường, trùng ID, nội dung quá ngắn); freshness kiểm tra độ mới theo thời gian. Một bản ghi có thể đúng cấu trúc nhưng vẫn stale.
4. **Cùng test set:** kiểm soát biến đầu vào để chênh lệch metric chỉ phản ánh corruption hoặc repair.
5. **Repair thành công:** quality/freshness phục hồi (PASS, FRESH) và metric repaired đạt lại baseline trên cùng test set.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` | 1.000 | 0.500 | 1.000 | |
| `mean_token_f1`      | 1.000 | 0.672 | 1.000 | |
| `judge_accuracy`     | 1.000 | 0.700 | 1.000 | |
| `mean_judge_score`   | 5 | 3.600 | 5 | |
| Quality checks         | PASS | FAIL | PASS | Duplicate và blank summary bị phát hiện |
| Freshness status       | FRESH | STALE | FRESH | Tỷ lệ stale 0.042 / 0.318 / 0.042 |

### Kết luận từ số liệu

1. Duplicate rows + blank summary + stale date → Quality Gate FAIL (unique `paper_id`, độ dài `summary`) và freshness STALE → Hit Rate 1.000 → 0.500, Token F1 1.000 → 0.672.
2. Repair từ raw → Quality Gate PASS, FRESH → metric repaired bằng baseline.

Corruption ảnh hưởng rõ nhất tới tín hiệu quan sát là **duplicate rows** và **blank summary**, vì đó là hai lỗi bị GX bắt trực tiếp; stale date được phát hiện qua freshness.

Kết quả khác kỳ vọng: **inject noise** và **truncate title** vừa không trúng tài liệu nào trong test set (không đổi metric), vừa không vi phạm expectation nào trong 4 expectations bắt buộc, nên lọt qua Quality Gate; cần thêm expectation cho độ dài `title` và ký tự rác.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Artifact và schema ổn định giúp các thành viên tích hợp độc lập dễ hơn.
2. Data quality và freshness cần được đo riêng để chẩn đoán lỗi rõ ràng.
3. Test set phải xây từ dữ liệu thật; metadata thiếu sẽ thu hẹp phạm vi đánh giá RAG.

### Nếu có thêm thời gian

Thêm expectation `ExpectColumnValueLengthsToBeBetween("title", min_value=10)` và regex chặn ký tự rác, rồi đo số kịch bản corruption bị Quality Gate phát hiện (hiện tại 3/6 tính cả freshness). Viết unit test cho quality, freshness, report và test set.

## 10. Cam kết của thành viên

- [ ] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [ ] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [ ] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [ ] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [ ] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [ ] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Công Vinh
**Ngày xác nhận:** 2026-09-25
