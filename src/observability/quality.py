from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import great_expectations as gx
import pandas as pd

from core.config import Settings
from core.utils import write_json


MIN_ROWS = 5
MAX_ROWS = 5000


def _quality_report_path(settings: Settings, report_name: str) -> Path:
    known_paths = {
        "baseline": settings.paths.baseline_quality_report,
        "corrupted": settings.paths.corrupted_quality_report,
    }
    return known_paths.get(report_name, settings.paths.quality_dir / f"{report_name}_quality_report.json")


def _expectations() -> list[Any]:
    return [
        gx.expectations.ExpectTableRowCountToBeBetween(
            min_value=MIN_ROWS,
            max_value=MAX_ROWS,
        ),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="paper_id"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="title"),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="text_for_embedding"),
        gx.expectations.ExpectColumnValuesToBeUnique(column="paper_id"),
        gx.expectations.ExpectColumnValueLengthsToBeBetween(
            column="summary",
            min_value=30,
        ),
    ]


def _serialize_validation(result: Any) -> dict[str, Any]:
    if hasattr(result, "to_json_dict"):
        return result.to_json_dict()
    if isinstance(result, dict):
        return result
    return {"success": False, "exception_info": {"exception_message": str(result)}}


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run the required Great Expectations 1.x checks and persist the result."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("run_data_quality_checks expects a pandas DataFrame.")

    context = gx.get_context(mode="ephemeral")
    data_source = context.data_sources.add_pandas(name="papers_source")
    data_asset = data_source.add_dataframe_asset(name="papers_asset")
    batch_definition = data_asset.add_batch_definition_whole_dataframe("papers_batch")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

    validations: list[dict[str, Any]] = []
    for expectation in _expectations():
        try:
            result = batch.validate(expectation)
            validations.append(_serialize_validation(result))
        except Exception as exc:  # Missing columns should become a visible failed check.
            validations.append(
                {
                    "success": False,
                    "expectation_type": expectation.expectation_type,
                    "exception_info": {
                        "raised_exception": True,
                        "exception_message": str(exc),
                    },
                }
            )

    payload: dict[str, Any] = {
        "report_name": report_name,
        "generated_at": datetime.now(UTC).isoformat(),
        "success": all(item.get("success", False) for item in validations),
        "row_count": int(len(df)),
        "expectations": validations,
    }
    write_json(_quality_report_path(settings, report_name), payload)
    return payload


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Build and persist a freshness SLA report for a cleaned dataframe."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("build_freshness_report expects a pandas DataFrame.")

    total_rows = int(len(df))
    if "age_days" in df.columns:
        age_days = pd.to_numeric(df["age_days"], errors="coerce")
    elif "published" in df.columns:
        published = pd.to_datetime(df["published"], errors="coerce", utc=True)
        today = pd.Timestamp.now(tz="UTC").normalize()
        age_days = (today - published.dt.normalize()).dt.days
    else:
        age_days = pd.Series(dtype="float64")

    stale_mask = age_days > settings.freshness_threshold_days
    stale_rows = int(stale_mask.fillna(False).sum())
    stale_ratio = stale_rows / total_rows if total_rows else 0.0

    published_values = pd.to_datetime(df.get("published", pd.Series(dtype="object")), errors="coerce", utc=True)
    valid_published = published_values.dropna()
    latest_published = valid_published.max().date().isoformat() if not valid_published.empty else None
    oldest_published = valid_published.min().date().isoformat() if not valid_published.empty else None

    payload: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "stale_ratio": stale_ratio,
        "threshold_days": settings.freshness_threshold_days,
        "max_stale_ratio": 0.25,
        "is_fresh": stale_ratio <= 0.25,
    }
    write_json(Path(report_path), payload)
    return payload
