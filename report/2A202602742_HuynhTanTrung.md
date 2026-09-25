# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin       | Nội dung                                              |
| --------------- | ----------------------------------------------------- |
| Họ và tên       | Huỳnh Tấn Trung                                       |
| MSSV            | 2A202602742                                           |
| Khóa/Lớp        | K4                                                    |
| Tên nhóm        | K4-L3-DAY10-P4P                                       |
| Vai trò chính   | RAG & Vector Specialist                               |
| Repository      | https://github.com/nguyenbien8/K4-L3-P4P-DataPipeline |
| Ngày hoàn thành | 2026-09-25                                            |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable           | File/hàm phụ trách                                                      | Input nhận vào                        | Output bàn giao                                                               | Trạng thái |
| ---------------------------- | ----------------------------------------------------------------------- | ------------------------------------- | ----------------------------------------------------------------------------- | ---------- |
| Embedding và ChromaDB index  | `src/retrieval/embeddings.py`, `src/retrieval/index.py`                 | clean dataframe, `text_for_embedding` | `papers-baseline`, `papers-corrupted`, `papers-repaired`; embedding manifests | Hoàn thành |
| Search, lookup và QA context | `src/retrieval/qa.py`, `src/retrieval/agent.py`, `src/retrieval/llm.py` | query, collection, test set           | search results, exact lookup, QA contexts, mock provider                      | Hoàn thành |

Chỉ nhận ownership cho phần bạn trực tiếp thực hiện. Liên hệ rõ phần việc của bạn với đầu vào, đầu ra và các thành viên phụ thuộc vào phần đó.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                   | Thành viên/module được hỗ trợ                                 | Kết quả                                                                           |
| --------------------------- | ------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Debug và tích hợp retrieval | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` | Baseline và corruption flow chạy exit code 0; ba collection được tạo và đánh giá. |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện                                        | File/hàm/artifact liên quan                             | Kết quả bàn giao                                                                     | Cách xác minh                                                           |
| ------------------------------------------------------------ | ------------------------------------------------------- | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------- |
| Xây dựng embedding và index ChromaDB bằng `all-MiniLM-L6-v2` | `src/retrieval/embeddings.py`, `src/retrieval/index.py` | Index 24 tài liệu trong `papers-baseline`; tạo được cả collection corrupted/repaired | `python script/run_phase1.py` và `python script/run_corruption_flow.py` |
| Kiểm tra retrieval và QA                                     | `src/retrieval/qa.py`, `src/retrieval/llm.py`           | Search trả kết quả, lookup theo DOI hoạt động, mock provider chạy offline            | Smoke test search/lookup/QA và `data/results/*_answers.json`            |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

`papers-baseline` chứa 24 documents; retrieval hit rate đạt `1.000`, giảm còn `0.900` trên corrupted và phục hồi về `1.000` trên repaired.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Phần retrieval biến dữ liệu sạch thành vector index có thể truy vấn, sau đó cung cấp context và metadata cho QA/evaluation. Mục tiêu là giữ cùng contract cho baseline, corrupted và repaired để so sánh công bằng.

### Cách triển khai

Embedding dùng `sentence-transformers/all-MiniLM-L6-v2` với vector được chuẩn hóa. ChromaDB lưu document content, metadata và cosine distance. `search` chuyển distance thành similarity score; `lookup` hỗ trợ exact paper ID/title; QA ưu tiên exact title match rồi mới semantic search. Mock LLM được dùng để kiểm tra offline khi không có API key.

### Input, output và contract

| Thành phần              | Mô tả                                                                                                   |
| ----------------------- | ------------------------------------------------------------------------------------------------------- |
| Input                   | Clean dataframe với `paper_id`, `title`, `text_for_embedding`                                           |
| Output                  | Chroma collections, embedding manifests, `SearchResult`, QA contexts                                    |
| Module phụ thuộc        | `core.config`, `core.utils`, ChromaDB, Sentence Transformers                                            |
| Module sử dụng output   | `evaluation.metrics`, `retrieval.qa`, `pipelines.phase1`, `pipelines.corruption_flow`                   |
| Điều kiện lỗi cần xử lý | Collection không tồn tại, query không có kết quả, provider thiếu credential; mock dùng cho offline test |

### Cách xác minh

```bash
python script/run_phase1.py
python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Tạo index 24 documents và đánh giá được ba trạng thái.
- **Kết quả thực tế:** Baseline và repaired hit rate `1.000`; corrupted hit rate `0.900`.
- **Artifact/log:** `data/chroma/`, `data/embeddings/`, `data/results/*_metrics.json`, `data/reports/*.md`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần tách index baseline, corrupted và repaired nhưng vẫn dùng chung code build.
- **Các phương án đã cân nhắc:** Dùng một collection rồi ghi đè; hoặc ánh xạ output manifest sang collection riêng.
- **Phương án đã chọn:** Dùng ba collection `papers-baseline`, `papers-corrupted`, `papers-repaired`.
- **Lý do:** Không ghi đè dữ liệu, dễ tái lập và so sánh cùng test set.
- **Bằng chứng quyết định phù hợp:** `data/embeddings/papers_embeddings*.json` ghi đúng collection; flow đánh giá đủ ba trạng thái.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `ModuleNotFoundError: No module named 'core'` khi chạy Python hệ thống.
- **Lệnh hoặc bước tái hiện:** Chạy smoke test bằng `python -c ...` ngoài môi trường dự án.
- **Nguyên nhân gốc:** Package dùng `src` layout và môi trường Python hệ thống chưa cài editable package.
- **Cách xử lý:** Dùng `.venv\Scripts\python.exe` đã cài dependencies của project.
- **Cách xác minh sau khi sửa:** `python script/run_phase1.py` và `python script/run_corruption_flow.py` đều exit code 0.
- **Điều học được:** Phải kiểm tra đúng interpreter trước khi kết luận lỗi thuộc code.

Nếu chưa xử lý xong:

- **Phạm vi bị ảnh hưởng:** [Module/artifact.]
- **Những gì đã loại trừ:** [Các giả thuyết đã kiểm tra.]
- **Bước tiếp theo:** [Hành động có thể kiểm chứng.]

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**

1. Crossref được parse thành raw records, cleaning tạo `text_for_embedding`, sau đó MiniLM tạo vector và ChromaDB lưu content cùng metadata.
2. Mỗi câu hỏi có `ground_truth_doc_ids`; retrieval hit rate kiểm tra document đúng có nằm trong kết quả, còn answer metrics so sánh câu trả lời với ground truth.
3. Quality checks kiểm tra schema, null, uniqueness và độ dài summary; freshness theo dõi tuổi dữ liệu qua `age_days` và tỷ lệ bài cũ.
4. Dùng cùng test set để mọi thay đổi metric phản ánh chất lượng dữ liệu/index, không phải do đề khác nhau.
5. Repair thành công khi quality gate pass, artifacts repaired được tạo từ raw và metric phục hồi; ở đây hit rate phục hồi từ `0.900` lên `1.000`.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal        | Baseline | Corrupted | Repaired | Nhận xét của cá nhân                                   |
| -------------------- | -------: | --------: | -------: | ------------------------------------------------------ |
| `retrieval_hit_rate` |    1.000 |     0.900 |    1.000 | Corruption làm mất một hit; repair phục hồi hoàn toàn. |
| `mean_token_f1`      |    0.612 |     0.587 |    0.612 | Chất lượng answer giảm nhẹ rồi phục hồi.               |
| `judge_accuracy`     |    0.600 |     0.600 |    0.600 | Không thay đổi trong lần đánh giá này.                 |
| `mean_judge_score`   |    3.200 |     3.200 |    3.200 | Không thay đổi trong lần đánh giá này.                 |
| Quality checks       |     True |     False |     True | Corrupted fail uniqueness và summary length.           |
| Freshness status     |     True |      True |     True | Stale ratio đều không vượt ngưỡng 25%.                 |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. Duplicate/blank-summary/drop-latest corruption → quality gate từ `True` thành `False` trong khi freshness vẫn `True` → hit rate giảm từ `1.000` xuống `0.900`, token F1 giảm từ `0.612` xuống `0.587`.
2. Rebuild từ raw records → quality gate repaired thành `True` → hit rate và token F1 phục hồi về baseline.

Corruption nào ảnh hưởng rõ nhất và vì sao?

Drop latest và các thay đổi làm mất hoặc làm yếu nội dung ảnh hưởng rõ nhất đến retrieval; bằng chứng là hit rate giảm 10% và quality gate phát hiện duplicate/summary ngắn.

Kết quả nào khác với kỳ vọng ban đầu?

Freshness vẫn `True` sau corruption vì stale-date chỉ tác động một phần nhỏ dữ liệu, dưới ngưỡng 25%. Đã kiểm tra trực tiếp `freshness_report.json` và quality report của corrupted.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Vector index phải có manifest và collection name rõ ràng để tái lập.
2. Quality gate và freshness đo hai rủi ro khác nhau; dữ liệu có thể còn fresh nhưng vẫn sai schema.
3. Corruption nhỏ ở dữ liệu đầu vào có thể làm giảm retrieval và answer quality dù agent vẫn trả lời được.

### Nếu có thêm thời gian

Thêm test tự động cho từng corruption type và ngưỡng metric; đo bằng coverage, quality-gate detection rate và chênh lệch hit rate trước/sau corruption.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Huỳnh Tấn Trung
**Ngày xác nhận:** 2026-09-25
