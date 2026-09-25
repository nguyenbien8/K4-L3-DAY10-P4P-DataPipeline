# Phase 1 — Baseline Report

## Source summary

| Field | Value |
|---|---|
| `source_api` | https://api.crossref.org/works |
| `source_query` | agentic retrieval augmented generation large language model |
| `source_filter` | from-pub-date:2026-03-29,has-abstract:true |
| `raw_mode` | loaded from crossref_records.json |
| `raw_records` | 24 |
| `clean_rows` | 24 |
| `run_date` | 2026-09-25T10:43:29.093717+00:00 |
| `embedding_model` | sentence-transformers/all-MiniLM-L6-v2 |
| `collection_name` | papers-baseline |
| `llm_provider` | gemini |
| `llm_model` | gemini-flash-lite-latest |

## Evaluation metrics

| Metric | Value |
|---|---|
| `samples` | 10 |
| `retrieval_hit_rate` | 1.0000 |
| `mean_token_f1` | 1.0000 |
| `judge_accuracy` | 1.0000 |
| `mean_judge_score` | 5 |
| `judge_fallback_count` | 0 |

## Data quality

Overall status: **PASS**; rows: `24`.

| Expectation | Status |
|---|---|
| `expect_table_row_count_to_be_between` | PASS |
| `expect_column_values_to_not_be_null` | PASS |
| `expect_column_values_to_not_be_null` | PASS |
| `expect_column_values_to_not_be_null` | PASS |
| `expect_column_values_to_be_unique` | PASS |
| `expect_column_value_lengths_to_be_between` | PASS |

## Freshness

- Status: **FRESH**
- Published range: `2026-03-28` → `2026-07-22`
- Stale rows: `1`/`24` (ratio `0.0417`; threshold `180` days)
