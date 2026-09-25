# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin       | Nội dung                                                    |
| --------------- | ----------------------------------------------------------- |
| Họ và tên       | Nguyễn Công Vinh                                            |
| MSSV            | 2A202602519                                                 |
| Khóa/Lớp        | K4                                                          |
| Tên nhóm        | P4P                                                         |
| Vai trò chính   | Observability & Evaluation                                  |
| Repository      | https://github.com/nguyenbien8/K4-L3-DAY10-P4P-DataPipeline |
| Ngày hoàn thành | 2026-09-25                                                  |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable  | File/hàm phụ trách                                      | Input nhận vào              | Output bàn giao                                                  | Trạng thái |
| ------------------- | ------------------------------------------------------- | --------------------------- | ---------------------------------------------------------------- | ---------- |
| Quality Gate GX 1.x | `src/observability/quality.py::run_data_quality_checks` | DataFrame + settings        | `data/quality/{baseline,corrupted,repaired}_quality_report.json` | Hoàn thành |
| Freshness SLA       | `src/observability/quality.py::build_freshness_report`  | Cột `age_days`/`published`  | `data/quality/*freshness_report.json`                            | Hoàn thành |
| Test set benchmark  | `src/evaluation/testset.py::build_test_set`             | DataFrame sạch              | `data/eval/test_set.json` (10 câu)                               | Hoàn thành |
| Báo cáo Markdown    | `src/observability/reporting.py`                        | metrics, quality, freshness | `data/reports/phase1_report.md`, `corruption_report.md`          | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                                                                           | Thành viên/module được hỗ trợ    | Kết quả                                    |
| ----------------------------------------------------------------------------------- | -------------------------------- | ------------------------------------------ |
| Đối chiếu dữ liệu Crossref trong `data/raw` để thiết kế câu hỏi                     | Lê Đức Tùng                      | Câu hỏi bám đúng trường có trong dữ liệu   |
| Thống nhất khóa `question_type`, `ground_truth_doc_ids` với `evaluation/metrics.py` | Nguyễn Văn Biển, Huỳnh Tấn Trung | `evaluate_pipeline` đọc test set không lỗi |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao                                | Cách xác minh                                                            |
| --------------------- | --------------------------- | ----------------------------------------------- | ------------------------------------------------------------------------ |
| Quality Gate GX 1.x   | `quality.py`                | Baseline PASS, corrupted FAIL, repaired PASS    | Các file `baseline_quality_report.json`,` corrupted_quality_report.json` |
| Freshness SLA         | `quality.py`                | Baseline FRESH, corrupted STALE, repaired FRESH | Các file `freshness_report.json`,` corrupted_freshness_report.json`      |
| Test set 10 câu       | `testset.py`                | summary 3, authors 3, date 2, categories 2      | Guide Bước 5: `Sinh được 10 câu hỏi test`                                |
| Báo cáo tự động       | `reporting.py`              | Bảng 3 trạng thái + phân tích tính từ số liệu   | `data/reports/corruption_report.md`                                      |

Output cụ thể: trên dữ liệu corrupted, Quality Gate phát hiện hai expectations không đạt: tính duy nhất của `paper_id` và độ dài tối thiểu của `summary`. Dataset corrupted có 22 dòng; freshness ghi nhận 7/22 dòng stale, tỷ lệ `0.3182` vượt SLA `0.25`. Sau repair, dữ liệu trở lại 24 dòng, Quality Gate PASS và freshness FRESH.

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

| Thành phần              | Mô tả                                                                                                                                                                                                                                                               |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Input                   | DataFrame sạch/bẩn/repaired (cột `paper_id`, `title`, `summary`, `text_for_embedding`, `age_days`, `published`), `Settings`                                                                                                                                         |
| Output                  | Quality report `{report_name, success, row_count, expectations[]}`; freshness `{latest_published, oldest_published, stale_rows, total_rows, stale_ratio, threshold_days, is_fresh}`; test set `[{id, question_type, question, ground_truth, ground_truth_doc_ids}]` |
| Module phụ thuộc        | `ingestion/cleaning.py` (schema), `core/config.py` (đường dẫn, ngưỡng 180 ngày)                                                                                                                                                                                     |
| Module sử dụng output   | `pipelines/phase1.py`, `pipelines/corruption_flow.py`, `evaluation/metrics.py`                                                                                                                                                                                      |
| Điều kiện lỗi cần xử lý | Thiếu cột; DataFrame rỗng; không đủ tài liệu cho một dạng câu hỏi; không có category                                                                                                                                                                                |

### Cách xác minh

```powershell
python -c "from core.config import load_settings; from observability.quality import run_data_quality_checks; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); res=run_data_quality_checks(df, s, 'test'); print('Quality check status =', res['success'])"
python -c "from core.config import load_settings; from evaluation.testset import build_test_set; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); ts=build_test_set(df, s.paths.eval_testset); print('Số câu hỏi test =', len(ts))"
python script/run_phase1.py
python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** `Quality check status = True`, `Sinh được 10 câu hỏi test`.
- **Kết quả thực tế:** `Quality check status = True`, `Sinh được 10 câu hỏi test`.
- **Kết quả artifact tích hợp:** Baseline quality PASS trên 24 dòng; corrupted quality FAIL trên 22 dòng; repaired quality PASS trên 24 dòng. Bộ metrics có đủ ba trạng thái.
- **Artifact/log:** `data/quality/`, `data/eval/test_set.json`, `data/results/`, `data/reports/phase1_report.md`, `data/reports/corruption_report.md`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần so sánh tác động của corruption và repair mà không để thay đổi câu hỏi làm nhiễu kết quả.
- **Các phương án đã cân nhắc:** (a) sinh lại test set cho từng trạng thái; (b) chỉ đánh giá retrieval; (c) dùng một test set cố định có answer ground truth và document ID.
- **Phương án đã chọn:** (c), dùng chung `data/eval/test_set.json` gồm 10 câu cho baseline, corrupted và repaired.
- **Lý do:** Chênh lệch metric khi đó phản ánh thay đổi dữ liệu/index thay vì thay đổi benchmark.
- **Bằng chứng quyết định phù hợp:** cùng 10 samples cho cả ba file metrics; Hit Rate giảm `1.0 → 0.9` khi corrupt và phục hồi `0.9 → 1.0` sau repair.
- **Điều kiện dữ liệu:** snapshot tích hợp hiện có category cho cả 24 bản ghi, vì vậy test set tạo đủ bốn nhóm theo tỷ lệ 3 summary, 3 authors, 2 date và 2 categories mà không có ground truth rỗng.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `FileNotFoundError: ...data\clean\papers_clean.json does not exist` khi chạy Quality Gate.
- **Lệnh hoặc bước tái hiện:** Chạy trực tiếp `pd.read_json(s.paths.clean_json)` trước khi tạo artifact của bước cleaning.
- **Nguyên nhân gốc:** Quality Gate phụ thuộc output của CP1, nhưng `papers_clean.json` chưa được sinh.
- **Cách xử lý:** Đọc `crossref_records.json`, gọi `build_clean_dataframe(...)`, sau đó ghi `papers_clean.csv` và `papers_clean.json` trước khi chạy quality check.
- **Cách xác minh sau khi sửa:** `Test-Path data/clean/papers_clean.json` trả `True`; Quality Gate trả `success=True` trên 24 dòng.
- **Điều học được:** Mỗi checkpoint phải kiểm tra đầy đủ artifact đầu vào thay vì chỉ kiểm tra code của module đang phụ trách.

## 7. Hiểu biết về luồng end-to-end

1. **Crossref → Chroma:** raw JSON được parse và lưu; cleaning chuẩn hóa trường và tạo `text_for_embedding`; Quality Gate kiểm tra; embedding MiniLM cùng metadata và document ID được nạp vào Chroma.
2. **Evaluation set:** `ground_truth_doc_ids` dùng để kiểm tra tài liệu đúng có trong top-4 kết quả hay không (Hit Rate); `ground_truth` dùng cho Token F1 và LLM Judge.
3. **Quality vs freshness:** quality kiểm tra cấu trúc và tính hợp lệ (thiếu trường, trùng ID, nội dung quá ngắn); freshness kiểm tra độ mới theo thời gian. Một bản ghi có thể đúng cấu trúc nhưng vẫn stale.
4. **Cùng test set:** kiểm soát biến đầu vào để chênh lệch metric chỉ phản ánh corruption hoặc repair.
5. **Repair thành công:** quality/freshness phục hồi (PASS, FRESH) và metric repaired đạt lại baseline trên cùng test set.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal        | Baseline | Corrupted | Repaired | Nhận xét của cá nhân                             |
| -------------------- | -------: | --------: | -------: | ------------------------------------------------ |
| `retrieval_hit_rate` |   1.0000 |    0.5000 |   1.0000 | Giảm 0.50 rồi phục hồi hoàn toàn                 |
| `mean_token_f1`      |   1.0000 |    0.6720 |   1.0000 | Giảm 0.328 rồi trở lại baseline                  |
| `judge_accuracy`     |   1.0000 |    0.7000 |   1.0000 | Giảm 0.30 rồi phục hồi hoàn toàn                 |
| `mean_judge_score`   |   5.0000 |    3.6000 |   5.0000 | Giảm 1.40 rồi phục hồi hoàn toàn                 |
| Quality checks       |     PASS |      FAIL |     PASS | Duplicate và blank summary bị phát hiện          |
| Freshness status     |    FRESH |     STALE |    FRESH | Tỷ lệ stale lần lượt là 0.0417, 0.3182 và 0.0417 |

### Kết luận từ số liệu

1. Duplicate rows, blank summary và stale date làm Quality Gate FAIL, freshness chuyển sang STALE; đồng thời Hit Rate giảm `1.0000 → 0.5000` và Token F1 giảm `1.0000 → 0.6720`.
2. Repair từ raw đưa Quality Gate về PASS, freshness về FRESH và toàn bộ bốn metric trở lại đúng mức baseline.

Corruption ảnh hưởng rõ nhất tới tín hiệu quan sát là **duplicate rows** và **blank summary**, vì đây là hai lỗi làm các quality checks thất bại.

Kết quả cần lưu ý: `inject_noise` và `truncate_title` không thuộc phạm vi bốn loại expectation bắt buộc, nên cần thêm kiểm tra độ dài title và ký tự rác nếu muốn Quality Gate phát hiện trực tiếp hai lỗi này.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Artifact và schema ổn định giúp các thành viên tích hợp độc lập dễ hơn.
2. Data quality và freshness cần được đo riêng để chẩn đoán lỗi rõ ràng.
3. Test set phải xây từ dữ liệu thật và được giữ cố định giữa các trạng thái để phép so sánh có ý nghĩa.

### Nếu có thêm thời gian

Bổ sung expectation về độ dài `title` và regex chặn ký tự rác, sau đó viết unit test cho quality, freshness, reporting và test-set generation. Có thể bật Ragas trong một lần chạy riêng để bổ sung metric nâng cao mà không làm chậm luồng kiểm thử mặc định.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Công Vinh

**MSSV:** 2A202602519

**Ngày xác nhận:** 2026-09-25
