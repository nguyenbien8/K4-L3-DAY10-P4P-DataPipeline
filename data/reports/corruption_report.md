# Corruption and Repair Report

## Executive comparison

| Metric | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|
| `retrieval_hit_rate` | 1.0000 | 0.5000 | 1.0000 |
| `mean_token_f1` | 1.0000 | 0.6720 | 1.0000 |
| `judge_accuracy` | 1.0000 | 0.7000 | 1.0000 |
| `mean_judge_score` | 5 | 3.6000 | 5 |

## Quality Gate comparison

| State | Status | Rows |
|---|---|---:|
| Baseline | PASS | - |
| Corrupted | FAIL | 22 |
| Repaired | PASS | 24 |

## Freshness comparison

### Corrupted

- Status: **STALE**
- Published range: `2025-03-28` → `2026-06-12`
- Stale rows: `7`/`22` (ratio `0.3182`; threshold `180` days)

### Repaired

- Status: **FRESH**
- Published range: `2026-03-28` → `2026-07-22`
- Stale rows: `1`/`24` (ratio `0.0417`; threshold `180` days)

## Interpretation

- **Detection:** the Quality Gate on corrupted data is **FAIL** (violated: `expect_column_values_to_be_unique` on `paper_id`, `expect_column_value_lengths_to_be_between` on `summary`).
- **Freshness:** corrupted data is **STALE** (stale ratio 0.3182 vs SLA 0.25); repaired data is **FRESH** (stale ratio 0.0417).
- `retrieval_hit_rate`: 1.0000 -> 0.5000 after corruption (change -0.5000), then fully recovered after repair (1.0000).
- `mean_token_f1`: 1.0000 -> 0.6720 after corruption (change -0.3280), then fully recovered after repair (1.0000).
- `judge_accuracy`: 1.0000 -> 0.7000 after corruption (change -0.3000), then fully recovered after repair (1.0000).
- `mean_judge_score`: 5.0000 -> 3.6000 after corruption (change -1.4000), then fully recovered after repair (5.0000).
- **Repair:** the repaired dataset is rebuilt from the raw snapshot (Quality Gate **PASS**), never patched from the corrupted dataframe, so re-running the flow yields the same result (idempotent).
