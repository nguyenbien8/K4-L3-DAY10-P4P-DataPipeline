# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Nguyễn Văn Biển            |
| MSSV               | 2A202602416                |
| Khóa/Lớp         | K4                         |
| Tên nhóm         | P4P                        |
| Vai trò chính    | Pipeline Lead & Integrator |
| Repository         | https://github.com/nguyenbien8/K4-L3-DAY10-P4P-DataPipeline |
| Ngày hoàn thành | 2026-09-25                 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Baseline pipeline | `src/pipelines/phase1.py::main`, `script/run_phase1.py` | Raw records, hàm của Người 2/3/4 | Clean, collection `papers-baseline`, `baseline_metrics.json`, `phase1_report.md` | Hoàn thành |
| Corruption/repair flow | `src/pipelines/corruption_flow.py::main`, `script/run_corruption_flow.py` | Artifact Phase 1 | `corrupted_metrics.json`, `repaired_metrics.json`, `corruption_report.md` | Hoàn thành |
| Cấu hình & tiện ích | `src/core/config.py`, `src/core/utils.py::write_dataframe` | `.env` | Đường dẫn artifact, lưu CSV + JSON | Hoàn thành |
| Tích hợp & nghiệm thu | Merge `main`, `docs/TEAM.md`, `report/group_report.md` | Nhánh của Người 2/3/4 | Repo nộp bài | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Merge nhánh `vinh/Observability-Evaluation` (GX 1.x) còn nằm ngoài `main` | Người 4 | `main` dùng đúng Great Expectations 1.x |
| Sửa manifest lưu đường dẫn tuyệt đối | Người 3 (`retrieval/index.py`) | `persist_path` = `data/chroma` |
| Chỉnh `corruption.py` theo Guide (drop 20%, title < 8 ký tự, lùi 365 ngày trên ~30% dòng) | Người 2 | Freshness chuyển STALE trên dữ liệu bẩn |
| Retry LLM Judge và đếm `judge_fallback_count` | Người 4 (`evaluation/metrics.py`) | Judge thật chấm điểm, số câu phải dùng heuristic được ghi lại |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Nối luồng baseline | `phase1.py` | Artifact Phase 1 đầy đủ | `python script/run_phase1.py` (exit 0) |
| Nối luồng corrupt → repair → so sánh | `corruption_flow.py` | Bảng 3 trạng thái trên console và `corruption_report.md` | `python script/run_corruption_flow.py` (exit 0) |
| Kiểm tra tín hiệu hoàn thành từng bước Guide | Guide Bước 1–8 | Tất cả đạt | Lệnh kiểm tra trong `docs/Guide.md` |

Output cụ thể: bảng in ra console khi chạy `run_corruption_flow.py`:

```text
Metric               | Baseline | Corrupted | Repaired
----------------------+----------+-----------+----------
retrieval_hit_rate   | 1.000    | 0.500     | 1.000
mean_token_f1        | 1.000    | 0.672     | 1.000
judge_accuracy       | 1.000    | 0.700     | 1.000
mean_judge_score     | 5.000    | 3.600     | 5.000
quality_gate_success | True     | False     | True
----------------------+----------+-----------+----------
```

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Các module (ingestion, quality, retrieval, evaluation) do 3 người khác viết. Cần một điểm điều phối chạy đúng thứ tự, lưu đúng artifact theo `core/config.py`, chặn dữ liệu xấu trước vector store, và chứng minh được Silent Failure cùng khả năng repair.

### Cách triển khai

- **Quality Gate trước index:** `phase1.py` chạy GX và freshness ngay sau cleaning; baseline fail thì dừng, dữ liệu xấu không vào ChromaDB.
- **Test set cố định:** chỉ sinh lần đầu (hoặc `REFRESH_TEST_SET=1`); nếu test set cũ trỏ tới `paper_id` không còn trong dữ liệu sạch thì tự sinh lại. Ba trạng thái đều đo trên cùng `test_set.json`.
- **Mỗi trạng thái một collection:** truyền đúng đường dẫn manifest vào `LocalEmbeddingIndex.build` để có `papers-baseline`, `papers-corrupted`, `papers-repaired`.
- **Corrupted vẫn được index dù gate fail:** production sẽ chặn ở đây, nhưng lab cần số liệu suy giảm nên chỉ ghi cảnh báo; nếu gate không phát hiện được lỗi thì in WARNING.
- **Idempotent Repair:** dựng lại từ `data/raw/crossref_records.json` bằng chính `build_clean_dataframe`, không vá dữ liệu hỏng; repaired fail gate thì dừng.
- **Demo agent không làm sập pipeline:** lỗi provider chỉ ghi vào `agent_demo_answers.json`.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | `data/raw/crossref_records.json`, biến môi trường `.env` |
| Output | `data/clean/`, `data/chroma/`, `data/embeddings/`, `data/eval/test_set.json`, `data/quality/`, `data/results/`, `data/reports/` |
| Module phụ thuộc | `ingestion.*`, `observability.*`, `evaluation.*`, `retrieval.index` |
| Module sử dụng output | `corruption_flow.py` dùng `baseline_metrics.json`, `papers_clean.json`, `test_set.json` của Phase 1 |
| Điều kiện lỗi cần xử lý | Thiếu artifact Phase 1 (báo rõ file thiếu); baseline fail gate; repaired fail gate; LLM provider lỗi |

### Cách xác minh

```bash
python script/run_phase1.py
python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** exit code 0, đủ artifact theo `docs/SUBMISSION.md`, corrupted giảm, repaired phục hồi.
- **Kết quả thực tế:** cả hai exit code 0; hit rate 1.000 → 0.500 → 1.000; Quality Gate PASS → FAIL → PASS.
- **Artifact/log:** `data/results/*_metrics.json`, `data/reports/phase1_report.md`, `data/reports/corruption_report.md`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Có nên dừng pipeline khi Quality Gate của dữ liệu corrupted fail?
- **Các phương án đã cân nhắc:** (a) dừng ngay như production; (b) vẫn index và đo để lấy số liệu suy giảm.
- **Phương án đã chọn:** (b) cho corrupted; (a) cho baseline và repaired.
- **Lý do:** Bài lab cần số liệu Silent Failure; còn baseline và repaired là dữ liệu phải tin cậy nên fail thì dừng.
- **Bằng chứng quyết định phù hợp:** corrupted vẫn được đo và cho `retrieval_hit_rate` 0.500 so với baseline 1.000, trong khi Quality Gate đã báo FAIL trước đó.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `agent_demo_answers.json` ghi `Error calling model 'gemini-2.5-flash' (NOT_FOUND): 404 NOT_FOUND ... This model models/gemini-2.5-flash is no longer available`; toàn bộ judge trả `Fallback heuristic judge used because the LLM evaluator was unavailable.`
- **Lệnh hoặc bước tái hiện:** `python script/run_phase1.py` với `LLM_MODEL=gemini-2.5-flash`.
- **Nguyên nhân gốc:** Model mặc định của repo đã bị gỡ; `metrics.py` bắt mọi exception và âm thầm dùng heuristic, nên `judge_accuracy` thực chất chỉ là Token F1 đổi thang.
- **Cách xử lý:** Liệt kê model khả dụng qua API, đổi sang `gemini-flash-lite-latest` (bản `gemini-flash-latest` hết hạn mức ngày của free tier) (`.env`, `.env.example`, `config.py`); thêm retry backoff 4 lần cho lỗi 503 và trường `judge_fallback_count` để lỗi không còn bị che.
- **Cách xác minh sau khi sửa:** `judge_fallback_count` = 0 / 0 / 0 cho 3 trạng thái: toàn bộ 30 lượt chấm do LLM thật.
- **Điều học được:** Fallback im lặng chính là một dạng Silent Failure ngay trong bộ đo; mọi fallback phải được đếm và báo cáo.

## 7. Hiểu biết về luồng end-to-end

1. **Crossref → vector index:** JSON Crossref được parse thành `PaperRecord` và lưu raw; cleaning tạo bảng một dòng mỗi bài với `text_for_embedding`; Quality Gate kiểm tra; MiniLM embed và nạp vào collection ChromaDB.
2. **Evaluation set:** mỗi câu gắn DOI đúng trong `ground_truth_doc_ids`. Retrieval hit khi DOI đó có trong top-4; Token F1 và LLM Judge so câu trả lời với `ground_truth` lấy từ dữ liệu sạch.
3. **Quality vs freshness:** quality kiểm tra tính hợp lệ của bảng (số dòng, null, trùng, độ dài summary); freshness kiểm tra độ mới theo thời gian (tỷ lệ bài > 180 ngày ≤ 25%). Dữ liệu có thể hợp lệ nhưng đã cũ.
4. **Cùng test set:** để chênh lệch giữa 3 trạng thái chỉ do dữ liệu, không do đề thi.
5. **Repair thành công:** dựa trên `repaired_quality_report.json` (PASS), `repaired_freshness_report.json` (FRESH) và `repaired_metrics.json` bằng `baseline_metrics.json`.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` | 1.000 | 0.500 | 1.000 | Giảm mạnh nhất, do tài liệu đúng bị drop |
| `mean_token_f1`      | 1.000 | 0.672 | 1.000 | |
| `judge_accuracy`     | 1.000 | 0.700 | 1.000 | |
| `mean_judge_score`   | 5 | 3.600 | 5 | |
| Quality checks         | PASS | FAIL | PASS | |
| Freshness status       | FRESH | STALE | FRESH | |

### Kết luận từ số liệu

1. Drop latest records + blank summary + duplicate rows → Quality Gate FAIL, freshness STALE → hit rate 1.000 → 0.500, Token F1 1.000 → 0.672.
2. Repair từ raw → Quality Gate PASS, FRESH → metrics repaired bằng baseline.

Corruption ảnh hưởng rõ nhất là **drop latest records**, vì tài liệu không còn trong kho thì không thể truy xuất được, trong khi agent vẫn trả lời bằng tài liệu khác.

Kết quả khác kỳ vọng ban đầu: judge baseline trước đây không phải điểm của LLM mà là heuristic, do model bị gỡ; chỉ phát hiện được khi đọc kỹ `reasoning` trong `baseline_answers.json`.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Người tích hợp phải kiểm tra artifact thực tế, không chỉ exit code: pipeline "chạy thành công" vẫn có thể cho số liệu sai.
2. Quality Gate phải đặt trước index; sau khi vào vector store, lỗi dữ liệu không còn nhìn thấy trực tiếp.
3. Repair đúng là tái tạo từ nguồn tin cậy, không phải vá dữ liệu hỏng.

### Nếu có thêm thời gian

Viết pytest cho `phase1.main` và `corruption_flow.main` với dữ liệu nhỏ và provider `mock`, chạy trên GitHub Actions; đo bằng coverage và thời gian phát hiện lỗi tích hợp.

## 10. Cam kết của thành viên

- [ ] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [ ] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [ ] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [ ] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [ ] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [ ] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Văn Biển
**Ngày xác nhận:** 2026-09-25
