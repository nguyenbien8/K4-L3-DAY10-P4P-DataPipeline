# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | K4                         |
| Tên nhóm         | P4P                        |
| Repository         | https://github.com/nguyenbien8/K4-L3-DAY10-P4P-DataPipeline |
| Ngày hoàn thành | 2026-09-25                 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Nguyễn Văn Biển | 2A202602416 | Pipeline Lead & Integrator | `src/core/`, `src/pipelines/`, `script/`, tích hợp cuối |
| 2 | Lê Đức Tùng | 2A202603005 | Data Foundation & Recovery | `src/ingestion/crossref.py`, `cleaning.py`, `corruption.py` |
| 3 | Huỳnh Tấn Trung | 2A202602742 | RAG & Vector Specialist | `src/retrieval/`, ChromaDB, LLM providers |
| 4 | Nguyễn Công Vinh | 2A202602519 | Observability & Evaluation | `src/observability/`, `src/evaluation/`, metrics/reports |

## 2. Tóm tắt kết quả

**Tóm tắt của nhóm:**

Nhóm hoàn thành đủ 7 tầng của pipeline: thu thập Crossref (Dual-Mode, snapshot 24 bài), làm sạch và mô hình hóa dữ liệu, Quality Gate bằng Great Expectations 1.x cùng Freshness SLA, index ChromaDB với MiniLM-L6-v2, đánh giá RAG trên test set cố định 10 câu, tiêm 6 dạng lỗi và Idempotent Repair. Cả `script/run_phase1.py` và `script/run_corruption_flow.py` đều chạy thành công (exit code 0) và sinh đủ artifact trong `data/`.

Baseline đạt `retrieval_hit_rate` = 1.000 và `mean_token_f1` = 1.000, Quality Gate `PASS`, dữ liệu `FRESH`. Sau khi tiêm lỗi, Quality Gate chuyển sang `FAIL` (vi phạm tính duy nhất `paper_id` và độ dài `summary`), freshness chuyển `STALE` (tỷ lệ bài cũ 0.318 > 0.25), và các chỉ số RAG giảm: hit rate còn 0.500, Token F1 còn 0.672. Agent vẫn trả lời bình thường mà không báo lỗi, đúng hiện tượng Silent Failure.

Corruption ảnh hưởng rõ nhất là **drop latest records** (xóa 20% bài mới nhất): 5/10 câu hỏi mất tài liệu đúng nên retrieval thất bại; **stale date** làm câu hỏi ngày `eval_008` trả sai. Các lỗi còn lại (blank summary, inject noise, truncate title) không trúng tài liệu cần cho câu trả lời nên không đổi metric, nhưng blank summary và duplicate rows bị Quality Gate bắt. Repair dựng lại dữ liệu từ raw snapshot, không vá dữ liệu hỏng; kết quả repaired phục hồi hoàn toàn về mức baseline (1.000 / 1.000).

Giới hạn còn lại: test set nhỏ (10 câu) và phần trả lời của `qa.py` lấy trực tiếp từ metadata nên Token F1 baseline rất cao; LLM Judge phụ thuộc hạn mức Gemini (số lần phải dùng judge dự phòng được ghi trong `judge_fallback_count`).

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API (hoặc snapshot data/raw/crossref_response.json)
    -> raw records (data/raw/crossref_records.json)
    -> cleaning và data modeling (data/clean/papers_clean.*)
    -> Quality Gate GX 1.x + Freshness SLA (data/quality/) -- FAIL thì dừng trước khi index
    -> test set cố định 10 câu (data/eval/test_set.json)
    -> embedding MiniLM + ChromaDB collection papers-baseline
    -> evaluation baseline (data/results/baseline_metrics.json) + phase1_report.md
    -> corruption 6 kịch bản -> Quality Gate (FAIL) -> papers-corrupted -> evaluate
    -> repair từ raw records -> Quality Gate (PASS) -> papers-repaired -> evaluate
    -> comparison report (data/reports/corruption_report.md)
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | Crossref REST API hoặc snapshot `data/raw/crossref_response.json` | Fetch, retry 429/5xx, fallback offline, parse, bỏ thẻ JATS | `data/raw/crossref_records.json` | Lê Đức Tùng |
| Cleaning          | `crossref_records.json` | Chuẩn hóa text, `age_days`, dedupe `paper_id`, `text_for_embedding` | `data/clean/papers_clean.{csv,json}` | Lê Đức Tùng |
| Embedding/index   | `text_for_embedding` | MiniLM-L6-v2, ChromaDB cosine, 3 collection tách biệt | `data/chroma/`, `data/embeddings/` | Huỳnh Tấn Trung |
| Evaluation        | clean dataframe | Test set 10 câu, Hit Rate, Token F1, LLM Judge | `data/eval/test_set.json`, `data/results/*_metrics.json` | Nguyễn Công Vinh |
| Observability     | clean/corrupted/repaired dataframe | Great Expectations 1.x (4 expectations) + Freshness SLA | `data/quality/*.json` | Nguyễn Công Vinh |
| Corruption/repair | clean dataframe, raw records | 6 kịch bản lỗi; repair dựng lại từ raw | `data/results/corruption_log.json`, `data/clean/*_corrupted.*`, `*_repaired.*` | Lê Đức Tùng |
| Orchestration     | `data/raw/crossref_records.json`, `data/eval/test_set.json` | `phase1.py` và `corruption_flow.py`: thứ tự chạy, Quality Gate trước index, test set cố định, 3 collection, so sánh 3 trạng thái | `data/results/*_metrics.json`, `data/reports/*.md` | Nguyễn Văn Biển |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | `gemini`            |
| `LLM_MODEL`                | `gemini-flash-lite-latest` |
| Embedding model              | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24 (`max_results`) |
| Retrieval `top_k`          | 4                   |
| Freshness threshold          | 180 ngày; `is_fresh = False` khi tỷ lệ bài cũ > 25% |
| Random seed                  | `random_state` 42–46 cho từng kịch bản corruption |

Không dán nội dung API key hoặc file `.env` vào báo cáo.

### Lệnh cài đặt

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

### Lệnh chạy

```bash
python script/run_phase1.py
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái | Thời điểm chạy gần nhất | Bằng chứng |
| ----------------- | ---------- | ----------------------- | ---------- |
| Baseline pipeline | Thành công (exit code 0) | 2026-09-25 10:34:44 UTC | `data/results/baseline_metrics.json`, `data/reports/phase1_report.md` |
| Corruption flow   | Thành công (exit code 0) | 2026-09-25 10:36:25 UTC | `data/results/{corrupted,repaired}_metrics.json`, `data/reports/corruption_report.md` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | Crossref REST API `https://api.crossref.org/works`; mặc định dùng snapshot offline `data/raw/crossref_response.json` |
| Query/filter                | query `agentic retrieval augmented generation large language model`; filter `from-pub-date:<run_date − 180 ngày>,has-abstract:true`; `rows=24` |
| Thời điểm lấy dữ liệu | Snapshot của starter repo (bài xuất bản 2026-03-28 → 2026-07-22) |
| Số record nhận được    | 24 item → 24 record hợp lệ |
| Cơ chế retry/backoff      | 3 lần, backoff 1s/2s khi gặp 429/500/502/503/504 hoặc lỗi mạng; thất bại thì fallback snapshot |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| `paper_id` | str (DOI, viết thường) | Có | Khóa duy nhất | Bỏ record; dedupe khi trùng |
| `title` | str | Có | Tiêu đề đã bỏ thẻ, gộp khoảng trắng | Bỏ record |
| `summary` | str | Có | Abstract đã bỏ thẻ JATS | Bỏ record; lọc khi quá ngắn |
| `authors_joined` | str | Không | Tác giả `given family`, nối bằng dấu phẩy | Chuỗi rỗng |
| `categories_joined` | str | Không | Lĩnh vực từ `subject` | Chuỗi rỗng |
| `published` | str `YYYY-MM-DD` | Có | Ngày xuất bản (ưu tiên `published` → `issued` → `created`) | Thiếu tháng/ngày điền 1; không có thì bỏ record |
| `age_days` | int | Có | `(run_date − published).days` | Tính lại mỗi lần chạy |
| `text_for_embedding` | str | Có | 5 dòng Title/Authors/Published/Categories/Summary | Luôn được sinh |

### Quy tắc cleaning

| Quy tắc                                 | Quality dimension liên quan | Số record bị tác động | Cách xác minh      |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Bỏ record thiếu DOI/title/abstract/ngày | Completeness | 0 | 24 item → 24 record |
| Bỏ thẻ HTML/JATS, gộp khoảng trắng | Validity | 24 | Không còn `<jats:p>` trong `papers_clean.json` |
| Dedupe theo `paper_id` | Uniqueness | 0 | GX `expect_column_values_to_be_unique` PASS |
| Lọc summary ≤ 10 ký tự | Completeness | 0 | Summary ngắn nhất ≥ 30 ký tự (GX PASS) |

`text_for_embedding` ghép 5 dòng `Title / Authors / Published / Categories / Summary` để embedding nắm được cả nội dung lẫn metadata. Document ID trong ChromaDB là `paper_id::index` (vẫn phân biệt được dòng trùng khi dữ liệu bị nhân bản), còn `paper_id` (DOI) nằm trong metadata để đối chiếu với `ground_truth_doc_ids`. `age_days` tính theo UTC từ `run_date` nên cùng một snapshot cho cùng giá trị trong một ngày chạy.

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | 10                         |
| Các `question_type`                   | `summary` 3, `authors` 3, `date` 2, `categories` 2 |
| Ground-truth document ID                 | DOI của bài được hỏi, lấy từ `paper_id`; mỗi câu một DOI khác nhau |
| Embedding model                          | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store/collection                  | ChromaDB persistent `data/chroma/`, cosine; `papers-baseline`, `papers-corrupted`, `papers-repaired` |
| Retrieval `top_k`                      | 4                          |
| LLM provider/model                       | Gemini `gemini-flash-lite-latest` (LLM Judge; có retry, fallback heuristic khi quá tải) |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` (chỉ sinh lần đầu hoặc khi `REFRESH_TEST_SET=1`) |

Test set được giữ nguyên khi đánh giá baseline, corrupted và repaired để mọi chênh lệch chỉ đến từ dữ liệu trong collection. Ground truth lấy từ dữ liệu sạch, nên khi dữ liệu bị lỗi thì câu trả lời lệch khỏi ground truth và phản ánh đúng mức suy giảm.

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/`                          | Có | `crossref_response.json`, `crossref_records.json` |
| Cleaned dataset          | `data/clean/`                        | Có | 24 dòng, CSV + JSON |
| Embedding manifest/index | `data/embeddings/`, `data/chroma/`   | Có | 3 manifest, `persist_path` tương đối |
| Evaluation set           | `data/eval/`                         | Có | 10 câu, 4 dạng |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có | Kèm `baseline_answers.json` |
| Quality/freshness        | `data/quality/`                      | Có | `baseline_quality_report.json`, `freshness_report.json` |
| Baseline report          | `data/reports/phase1_report.md`      | Có | Sinh tự động từ pipeline |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` | 1.000 | Tất cả câu hỏi đều truy xuất được tài liệu đúng trong top-4 |
| `mean_token_f1`      | 1.000 | Câu trả lời lấy trực tiếp từ metadata nên khớp ground truth |
| `judge_accuracy`     | 1.000 | Tỷ lệ câu LLM Judge đánh giá đúng |
| `mean_judge_score`   | 5 | Điểm trung bình thang 1–5 |
| Ragas                | N/A | Không bật (`RUN_RAGAS` chưa đặt) để tiết kiệm hạn mức LLM |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| `ExpectTableRowCountToBeBetween` | Volume | 5–5000 dòng | PASS (24) | `baseline_quality_report.json` |
| `ExpectColumnValuesToNotBeNull` (`paper_id`, `title`, `text_for_embedding`) | Completeness | Không null | PASS | `baseline_quality_report.json` |
| `ExpectColumnValuesToBeUnique` (`paper_id`) | Uniqueness | Không trùng | PASS | `baseline_quality_report.json` |
| `ExpectColumnValueLengthsToBeBetween` (`summary`) | Validity | ≥ 30 ký tự | PASS | `baseline_quality_report.json` |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | DataFrame sạch trước khi index (`data/quality/freshness_report.json`) |
| Timestamp mới nhất       | 2026-07-22 |
| Ngưỡng freshness         | 180 ngày; tối đa 25% bài quá hạn |
| Trạng thái baseline      | FRESH |
| Lý do                     | 1/24 bài quá 180 ngày (tỷ lệ 0.042 ≤ 0.25) |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| Drop latest records | Bỏ 20% bài có `age_days` nhỏ nhất | 5 | Row count giảm | Tài liệu đúng mất khỏi collection, hit rate giảm | Dựng lại từ raw |
| Blank summary | Gán `summary = ""` | 2 | Fail độ dài `summary` | GX FAIL `expect_column_value_lengths_to_be_between` | Dựng lại từ raw |
| Inject noise | Nối chuỗi rác vào `summary` | 2 | Không bắt được bằng 4 expectations | Nhiễu đi vào `text_for_embedding` | Dựng lại từ raw |
| Truncate title | Cắt `title` còn 6 ký tự | 2 | Không bắt được bằng 4 expectations | Tra cứu theo tên bài thất bại | Dựng lại từ raw |
| Stale date | Lùi `published` 365 ngày, cộng `age_days` | 6 | Freshness STALE | Tỷ lệ bài cũ 0.318 > 0.25 | Dựng lại từ raw |
| Duplicate rows | Nhân bản 3 dòng | 3 | Fail tính duy nhất `paper_id` | GX FAIL `expect_column_values_to_be_unique` | Dựng lại từ raw (dedupe) |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: Log có đủ 6 loại, mỗi mục ghi `type`, số dòng `rows` và danh sách `paper_ids` bị ảnh hưởng; tham số (tỷ lệ, seed) cố định trong `corruption.py`.

Repair không sửa từng dòng hỏng trên DataFrame corrupted mà bỏ toàn bộ dữ liệu đó và chạy lại `build_clean_dataframe(load_raw_records(data/raw/crossref_records.json))`, tức là dùng lại đúng hàm cleaning trên nguồn raw đáng tin cậy. Dữ liệu repaired phải qua Quality Gate lần nữa; nếu fail thì pipeline dừng thay vì báo phục hồi thành công. Vì nguồn raw không đổi nên chạy lại bao nhiêu lần cũng cho cùng kết quả (idempotent).

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   | 1.000 | 0.500 | 1.000 | -0.500 | 100% | Tài liệu đúng bị drop hoặc hỏng |
| `mean_token_f1`        | 1.000 | 0.672 | 1.000 | -0.328 | 100% | Summary rỗng/nhiễu làm lệch câu trả lời |
| `judge_accuracy`       | 1.000 | 0.700 | 1.000 | -0.300 | 100% | |
| `mean_judge_score`     | 5 | 3.600 | 5 | -1.400 | 100% | |
| Quality checks pass/fail | PASS | FAIL | PASS | PASS → FAIL | FAIL → PASS | Duplicate + blank summary bị GX phát hiện |
| Freshness status         | FRESH | STALE | FRESH | FRESH → STALE | STALE → FRESH | Stale date trên ~30% dòng vượt SLA |

Kết luận nhân quả:

1. Drop 20% bài mới nhất + blank summary + duplicate rows → Quality Gate `FAIL` (unique `paper_id`, độ dài `summary`) và freshness `STALE` → `retrieval_hit_rate` giảm từ 1.000 xuống 0.500, `mean_token_f1` từ 1.000 xuống 0.672, trong khi agent vẫn trả lời mà không báo lỗi.
2. Repair dựng lại từ `crossref_records.json` → Quality Gate `PASS`, freshness `FRESH` → metrics repaired bằng baseline (1.000 / 1.000).

## 11. Vấn đề tích hợp quan trọng

- **Triệu chứng:** LLM Judge luôn rơi vào chế độ dự phòng và demo agent báo lỗi; `judge_accuracy` thực chất là heuristic từ Token F1.
- **Nguyên nhân:** Model `gemini-2.5-flash` đã bị Google gỡ (404 NOT_FOUND); `metrics.py` bắt mọi exception và âm thầm chuyển sang heuristic, nên không ai thấy lỗi. Khi đổi model, Gemini thỉnh thoảng trả 503 do quá tải.
- **Cách xử lý:** Đổi `LLM_MODEL` sang `gemini-flash-lite-latest` (bản `gemini-flash-latest` hết hạn mức ngày của free tier; kiểm tra bằng danh sách model của API), thêm retry với exponential backoff (4 lần) cho judge, và ghi `judge_fallback_count` vào metrics để biết bao nhiêu câu phải dùng heuristic.
- **Cách xác minh:** `data/results/*_metrics.json` có `judge_fallback_count` = 1 (baseline), 0 (corrupted), 0 (repaired).

Các vấn đề tích hợp khác đã xử lý: nhánh Observability (GX 1.x) chưa được merge vào `main`; snapshot raw bị thay bằng dữ liệu live không có `categories` (đã khôi phục snapshot chuẩn); manifest embeddings chứa đường dẫn tuyệt đối `D:\...` (đã đổi sang đường dẫn tương đối).

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| `qa.py` trả lời bằng metadata, không sinh bằng LLM | Token F1 baseline gần tuyệt đối, chưa đo được hallucination của LLM | Thêm chế độ trả lời bằng LLM trên context truy xuất, so sánh Token F1 và judge giữa hai chế độ |
| Inject noise và truncate title không bị 4 expectations phát hiện | Một phần lỗi lọt qua Quality Gate | Thêm expectation độ dài `title` ≥ 10 ký tự và regex chặn ký tự rác; đo số kịch bản bị phát hiện (hiện 3/6) |
| Test set chỉ 10 câu | Mỗi câu chiếm 10% metric | Tăng lên 30–50 câu, báo cáo khoảng tin cậy |
| LLM Judge phụ thuộc hạn mức Gemini | Có thể phải dùng heuristic | Theo dõi `judge_fallback_count`, cache kết quả judge |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [ ] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
