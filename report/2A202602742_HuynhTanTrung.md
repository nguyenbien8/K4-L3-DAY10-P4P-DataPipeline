# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Huỳnh Tấn Trung            |
| MSSV               | 2A202602742                |
| Khóa/Lớp         | K4                         |
| Tên nhóm         | P4P                        |
| Vai trò chính    | RAG & Vector Specialist    |
| Repository         | https://github.com/nguyenbien8/K4-L3-DAY10-P4P-DataPipeline |
| Ngày hoàn thành | 2026-09-25                 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Embedding | `src/retrieval/embeddings.py`: `MiniLMEmbeddings` | `text_for_embedding` | Vector 384 chiều, chuẩn hóa L2 | Hoàn thành |
| Vector index ChromaDB | `src/retrieval/index.py`: `LocalEmbeddingIndex.build/load/search/lookup` | DataFrame sạch/bẩn/repaired | 3 collection `papers-baseline`, `papers-corrupted`, `papers-repaired` trong `data/chroma/`; manifest `data/embeddings/*.json` | Hoàn thành |
| QA & Agent đa provider | `src/retrieval/qa.py`, `agent.py`, `llm.py`, `__init__.py` | Câu hỏi, index | `AnswerResult` (câu trả lời + doc id truy xuất); agent LangChain với tool `semantic_search_papers`, `lookup_paper` | Hoàn thành |

`evaluation/metrics.py` (Người 4) gọi `answer_question` trên index của tôi để tính Hit Rate; `pipelines/*` (Người 1) gọi `LocalEmbeddingIndex.build` cho từng trạng thái.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Chạy thử pipeline và sinh bộ artifact đầu tiên (`data/chroma`, `data/results`) | Cả nhóm | Có artifact để các thành viên đối chiếu tín hiệu hoàn thành |
| Gộp xung đột khi merge các nhánh | Người 2, Người 4 | Commit `fix conflix` |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Index baseline | `index.py`, `data/chroma/` | Collection `papers-baseline` 24 docs | Log `[phase1] Index: 24 docs -> Chroma collection 'papers-baseline'` |
| Index corrupted/repaired tách biệt | `index.py::_derive_collection_name` | `papers-corrupted` 22 docs, `papers-repaired` 24 docs | Log `[flow] Evaluated collection ...` |
| Retrieval cho evaluation | `qa.py::answer_question` | Hit Rate baseline 1.000 | `data/results/baseline_metrics.json` |

Output cụ thể: ba collection độc lập trong cùng `data/chroma/`, mỗi lần build đều xóa rồi tạo lại collection nên không lẫn dữ liệu giữa các trạng thái.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Cần một vector store để RAG tìm đúng tài liệu cho mỗi câu hỏi, và phải cô lập dữ liệu của 3 trạng thái (sạch, bẩn, đã sửa) để so sánh công bằng.

### Cách triển khai

- **Embedding:** `sentence-transformers/all-MiniLM-L6-v2`, `normalize_embeddings=True`, model được cache bằng `lru_cache` để không tải lại nhiều lần.
- **Index:** ChromaDB `PersistentClient`, không gian `cosine`. Mỗi document có id `paper_id::index` (giữ được cả dòng trùng khi dữ liệu bị nhân bản) và metadata `paper_id`, `title`, `published`, `authors_joined`, `categories_joined`, `summary`, URL.
- **Tách collection:** tên collection suy ra từ đường dẫn manifest (`papers_embeddings.json` → `papers-baseline`, `_corrupted` → `papers-corrupted`, `_repaired` → `papers-repaired`).
- **QA:** nếu câu hỏi chứa tên bài trong dấu nháy đơn thì tra cứu chính xác (`lookup`) và đặt lên đầu, rồi bổ sung kết quả semantic search; câu trả lời lấy từ metadata theo loại câu hỏi (tác giả, ngày, lĩnh vực, câu đầu summary).
- **Đa provider:** `build_llm` hỗ trợ `gemini`, `openai`, `anthropic`, `openrouter`, `ollama`, `custom`, `mock`; chọn qua biến `LLM_PROVIDER`.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | DataFrame có `paper_id`, `title`, `text_for_embedding`, `published` (str), `authors_joined`, `categories_joined`, `summary`, `abs_url`, `pdf_url` |
| Output | Collection ChromaDB; manifest JSON (`collection_name`, `persist_path` tương đối, danh sách documents); `list[SearchResult]` |
| Module phụ thuộc | `ingestion/cleaning.py` (schema), `core/config.py` (tên collection, `top_k=4`) |
| Module sử dụng output | `evaluation/metrics.py`, `pipelines/phase1.py`, `pipelines/corruption_flow.py` |
| Điều kiện lỗi cần xử lý | Metadata kiểu Timestamp/None (Chroma không nhận); collection cũ còn tồn tại; manifest chứa đường dẫn máy khác |

### Cách xác minh

```bash
python script/run_phase1.py
python -c "import chromadb; c=chromadb.PersistentClient(path='data/chroma'); print({x.name: c.get_collection(x.name).count() for x in c.list_collections()})"
```

- **Kết quả mong đợi:** 3 collection, baseline và repaired 24 docs, corrupted ít hơn do bị drop.
- **Kết quả thực tế:** `papers-baseline` 24 docs, `papers-corrupted` 22 docs, `papers-repaired` 24 docs.
- **Artifact/log:** `data/chroma/`, `data/embeddings/papers_embeddings*.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lưu 3 trạng thái dữ liệu trong vector store như thế nào.
- **Các phương án đã cân nhắc:** (a) một collection, ghi đè mỗi lần chạy; (b) mỗi trạng thái một collection riêng.
- **Phương án đã chọn:** (b).
- **Lý do:** Ghi đè làm mất baseline để so sánh; tách collection cho phép đánh giá cả 3 trạng thái trên cùng test set và kiểm tra lại bất kỳ lúc nào.
- **Bằng chứng quyết định phù hợp:** baseline 1.000, corrupted 0.500, repaired 1.000 (Hit Rate) được đo độc lập.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Manifest `data/embeddings/papers_embeddings.json` chứa `"persist_path": "D:\\VinUni\\K4-L3-DAY10-P4P-DataPipeline\\data\\chroma"`.
- **Lệnh hoặc bước tái hiện:** chạy `run_phase1.py` rồi mở manifest.
- **Nguyên nhân gốc:** `LocalEmbeddingIndex.build` ghi `str(persist_path)` là đường dẫn tuyệt đối của máy chạy; file này được commit nên lộ đường dẫn cá nhân (bị trừ điểm) và `load()` hỏng trên máy khác.
- **Cách xử lý:** Ghi đường dẫn tương đối so với project root (`data/chroma`); khi `load()` gặp đường dẫn tuyệt đối không tồn tại thì quay về `settings.paths.chroma_dir`. (Người 1 hỗ trợ khi tích hợp.)
- **Cách xác minh sau khi sửa:** manifest mới ghi `"persist_path": "data/chroma"`.
- **Điều học được:** Artifact được commit cũng là mã nguồn; không được chứa thông tin phụ thuộc máy.

## 7. Hiểu biết về luồng end-to-end

1. **Crossref → vector index:** raw JSON → `PaperRecord` → DataFrame sạch với `text_for_embedding` → MiniLM embed → ChromaDB `papers-baseline`.
2. **Evaluation set:** mỗi câu có `ground_truth_doc_ids`; Hit Rate = tỷ lệ câu có DOI đúng trong top-4 kết quả; Token F1 và LLM Judge đo chất lượng câu trả lời.
3. **Quality vs freshness:** quality kiểm tra tính hợp lệ của dữ liệu trong bảng; freshness kiểm tra độ mới (tỷ lệ bài quá 180 ngày ≤ 25%).
4. **Cùng test set:** để chênh lệch chỉ đến từ dữ liệu trong collection, không phải từ câu hỏi.
5. **Repair thành công:** collection `papers-repaired` cho metrics bằng baseline, Quality Gate `PASS`.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.000 | 0.500 | 1.000 | Tài liệu đúng bị drop/biến đổi nên không còn trong top-4 |
| `mean_token_f1` | 1.000 | 0.672 | 1.000 | |
| `judge_accuracy` | 1.000 | 0.700 | 1.000 | |
| `mean_judge_score` | 5 | 3.600 | 5 | |
| Quality checks | PASS | FAIL | PASS | |
| Freshness status | FRESH | STALE | FRESH | |

### Kết luận từ số liệu

1. Drop latest records + blank summary → Quality Gate `FAIL` → collection `papers-corrupted` thiếu tài liệu đúng → Hit Rate giảm từ 1.000 xuống 0.500.
2. Repair từ raw → collection `papers-repaired` dựng lại đủ 24 docs → Hit Rate về 1.000.

Corruption ảnh hưởng rõ nhất tới retrieval là **drop latest records**: vector của bài bị xóa không còn trong collection, nên dù embedding tốt đến đâu cũng không tìm ra được.

Kết quả khác kỳ vọng: agent vẫn trả lời bình thường trên collection bẩn mà không báo lỗi, đúng hiện tượng Silent Failure; chỉ Quality Gate mới phát hiện được.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Cần cô lập vector store theo trạng thái dữ liệu thì mới so sánh được.
2. Quality Gate phải đặt trước bước index, vì sau khi vào vector store thì lỗi dữ liệu không còn nhìn thấy trực tiếp.
3. Retrieval tốt không bù được dữ liệu thiếu: tài liệu không có trong kho thì không thể được tìm thấy.

### Nếu có thêm thời gian

Thêm kiểm tra số document trong collection bằng số dòng DataFrame sau mỗi lần build, và thêm pytest cho `search`/`lookup`; đo bằng tỷ lệ build lỗi được phát hiện trước bước evaluate.

## 10. Cam kết của thành viên

- [ ] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [ ] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [ ] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [ ] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [ ] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [ ] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Huỳnh Tấn Trung
**Ngày xác nhận:** 2026-09-25
