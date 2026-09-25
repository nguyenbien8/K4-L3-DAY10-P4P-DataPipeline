from __future__ import annotations

from pathlib import Path
from datetime import timedelta

import pandas as pd

from core import utils


DROP_LATEST_FRACTION = 0.2
TRUNCATED_TITLE_CHARS = 6
STALE_DATE_FRACTION = 0.3
STALE_DATE_SHIFT_DAYS = 365


def _rebuild_text_for_embedding(df: pd.DataFrame) -> pd.DataFrame:
    """Rebuild the embedding text + summary_chars from the (possibly corrupted) columns."""
    df["summary"] = df["summary"].fillna("").astype(str)
    df["title"] = df["title"].fillna("").astype(str)
    df["authors_joined"] = df["authors_joined"].fillna("").astype(str)
    df["categories_joined"] = df["categories_joined"].fillna("").astype(str)
    df["published"] = df["published"].fillna("").astype(str)

    df["summary_chars"] = df["summary"].str.len()
    df["text_for_embedding"] = (
        "Title: " + df["title"] + "\n"
        + "Authors: " + df["authors_joined"] + "\n"
        + "Published: " + df["published"] + "\n"
        + "Categories: " + df["categories_joined"] + "\n"
        + "Summary: " + df["summary"]
    )
    return df


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: Path | str) -> pd.DataFrame:
    """Simulate 6 real-world data corruption patterns on a clean DataFrame.

    Corruption types (matches the lab spec):
      1. drop_latest_records  - drop 20% of the newest papers (by age_days)
      2. blank_summary        - blank summary on ~10% of rows
      3. inject_noise         - append garbage tokens to summary on ~10% of rows
      4. truncate_title       - cut title to < 8 chars on ~10% of rows
      5. stale_date           - push published date back 365 days on ~30% of rows
      6. duplicate_rows       - duplicate up to 3 rows

    The function always rebuilds `text_for_embedding` and `summary_chars` so the
    corrupted DataFrame stays schema-compatible with the clean one.
    """
    corrupted = df.copy(deep=True)
    log: list[dict[str, object]] = []

    if corrupted.empty:
        utils.write_json(Path(output_log_path), log)
        return corrupted

    # 1. Drop the newest 20% of records (smallest age_days = most recent)
    if "age_days" in corrupted.columns:
        corrupted = corrupted.sort_values(by="age_days").reset_index(drop=True)
        drop_count = max(1, round(len(corrupted) * DROP_LATEST_FRACTION))
        dropped_ids = corrupted.iloc[:drop_count]["paper_id"].tolist()
        corrupted = corrupted.iloc[drop_count:].reset_index(drop=True)
        log.append({
            "type": "drop_latest_records",
            "rows": drop_count,
            "paper_ids": dropped_ids,
        })

    if corrupted.empty:
        utils.write_json(Path(output_log_path), log)
        return corrupted

    # 2. Blank summary on ~10% of rows
    blank_idx = corrupted.sample(frac=0.1, random_state=42).index
    corrupted.loc[blank_idx, "summary"] = ""
    log.append({
        "type": "blank_summary",
        "rows": len(blank_idx),
        "paper_ids": corrupted.loc[blank_idx, "paper_id"].tolist(),
    })

    # 3. Inject noise into summary on ~10% of rows
    noise_idx = corrupted.sample(frac=0.1, random_state=43).index
    corrupted.loc[noise_idx, "summary"] = (
        corrupted.loc[noise_idx, "summary"].astype(str) + " [CORRUPTED_NOISE_!@#123]"
    )
    log.append({
        "type": "inject_noise",
        "rows": len(noise_idx),
        "paper_ids": corrupted.loc[noise_idx, "paper_id"].tolist(),
    })

    # 4. Truncate title to < 8 chars on ~10% of rows
    trunc_idx = corrupted.sample(frac=0.1, random_state=44).index
    corrupted.loc[trunc_idx, "title"] = (
        corrupted.loc[trunc_idx, "title"].astype(str).apply(lambda x: x[:TRUNCATED_TITLE_CHARS])
    )
    log.append({
        "type": "truncate_title",
        "rows": len(trunc_idx),
        "paper_ids": corrupted.loc[trunc_idx, "paper_id"].tolist(),
    })

    # 5. Push published date back 365 days. ~30% of rows so the Freshness SLA (>25% stale) is tripped
    old_date_idx = corrupted.sample(frac=STALE_DATE_FRACTION, random_state=45).index
    parsed = pd.to_datetime(corrupted.loc[old_date_idx, "published"], errors="coerce")
    corrupted.loc[old_date_idx, "published"] = (
        parsed - timedelta(days=STALE_DATE_SHIFT_DAYS)
    ).dt.strftime("%Y-%m-%d")
    if "age_days" in corrupted.columns:
        corrupted.loc[old_date_idx, "age_days"] = (
            corrupted.loc[old_date_idx, "age_days"] + STALE_DATE_SHIFT_DAYS
        )
    log.append({
        "type": "stale_date",
        "rows": len(old_date_idx),
        "paper_ids": corrupted.loc[old_date_idx, "paper_id"].tolist(),
    })

    # 6. Duplicate up to 3 rows
    dup_count = min(3, len(corrupted))
    dup_rows = corrupted.sample(n=dup_count, random_state=46)
    corrupted = pd.concat([corrupted, dup_rows], ignore_index=True)
    log.append({
        "type": "duplicate_rows",
        "rows": dup_count,
        "paper_ids": dup_rows["paper_id"].tolist(),
    })

    # Rebuild derived columns so the corrupted frame stays schema-compatible
    corrupted = _rebuild_text_for_embedding(corrupted)

    utils.write_json(Path(output_log_path), log)
    return corrupted