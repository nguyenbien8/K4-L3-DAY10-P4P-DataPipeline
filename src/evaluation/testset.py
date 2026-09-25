from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json


PREFERRED_QUESTION_COUNTS = {
    "summary": 3,
    "authors": 3,
    "date": 2,
    "categories": 2,
}

QUESTION_COUNTS_WITHOUT_CATEGORIES = {
    "summary": 4,
    "authors": 3,
    "date": 3,
}


def _value(row: dict[str, Any], key: str, fallback: str = "") -> str:
    value = row.get(key, fallback)
    if isinstance(value, list):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    if value is None or (not isinstance(value, (dict, tuple, set)) and pd.isna(value)):
        return ""
    return str(value).strip()


def _candidates(df: pd.DataFrame, question_type: str) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    for raw_row in df.to_dict(orient="records"):
        paper_id = _value(raw_row, "paper_id")
        title = _value(raw_row, "title")
        summary = _value(raw_row, "summary")
        authors = _value(raw_row, "authors_joined", _value(raw_row, "authors"))
        categories = _value(raw_row, "categories_joined", _value(raw_row, "categories"))
        published = _value(raw_row, "published")

        ground_truth_by_type = {
            "summary": first_sentence(summary),
            "authors": authors,
            "date": published,
            "categories": categories,
        }
        ground_truth = ground_truth_by_type[question_type]
        if paper_id and title and ground_truth:
            candidates.append(
                {
                    "paper_id": paper_id,
                    "title": title,
                    "ground_truth": ground_truth,
                }
            )
    return candidates


def _question_counts(df: pd.DataFrame) -> dict[str, int]:
    """Use all four types when source categories exist; otherwise avoid invented labels."""
    if len(_candidates(df, "categories")) >= PREFERRED_QUESTION_COUNTS["categories"]:
        return PREFERRED_QUESTION_COUNTS
    return QUESTION_COUNTS_WITHOUT_CATEGORIES


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Create a deterministic 10-question benchmark from available source fields."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("build_test_set expects a pandas DataFrame.")
    if df.empty:
        raise ValueError("Cannot build an evaluation set from an empty dataframe.")

    test_set: list[dict[str, Any]] = []
    used_document_ids: set[str] = set()
    next_id = 1
    for question_type, count in _question_counts(df).items():
        candidates = _candidates(df, question_type)
        if len(candidates) < count:
            raise ValueError(
                f"Not enough valid documents for '{question_type}': "
                f"expected {count}, found {len(candidates)}."
            )

        unused_candidates = [item for item in candidates if item["paper_id"] not in used_document_ids]
        selected_candidates = (unused_candidates or candidates)[:count]
        for candidate in selected_candidates:
            title = candidate["title"]
            question_templates = {
                "summary": f"What is the summary of the paper '{title}'?",
                "authors": f"Who authored the paper '{title}'?",
                "date": f"When was the paper '{title}' published?",
                "categories": f"What categories does the paper '{title}' belong to?",
            }
            test_set.append(
                {
                    "id": f"eval_{next_id:03d}",
                    "question_type": question_type,
                    "question": question_templates[question_type],
                    "ground_truth": candidate["ground_truth"],
                    "ground_truth_doc_ids": [candidate["paper_id"]],
                }
            )
            used_document_ids.add(candidate["paper_id"])
            next_id += 1

    write_json(output_path, test_set)
    return test_set
