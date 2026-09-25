from __future__ import annotations

from pathlib import Path
from typing import Any

from core.utils import write_text


def _display(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value).replace("|", "\\|").replace("\n", " ")


def _metric_rows(metrics: dict[str, Any]) -> list[str]:
    rows = []
    for key, value in metrics.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            rows.append(f"| `{key}` | {_display(value)} |")
    return rows


def _quality_status(quality: dict[str, Any]) -> str:
    return "PASS" if quality.get("success") else "FAIL"


def _quality_rows(quality: dict[str, Any]) -> list[str]:
    rows = []
    for item in quality.get("expectations", []):
        expectation = item.get("expectation_config", {}).get("type") or item.get("expectation_type", "unknown")
        rows.append(f"| `{expectation}` | {_quality_status(item)} |")
    return rows


def _freshness_summary(freshness: dict[str, Any]) -> str:
    return (
        f"- Status: **{'FRESH' if freshness.get('is_fresh') else 'STALE'}**\n"
        f"- Published range: `{_display(freshness.get('oldest_published'))}` → `{_display(freshness.get('latest_published'))}`\n"
        f"- Stale rows: `{_display(freshness.get('stale_rows'))}`/`{_display(freshness.get('total_rows'))}` "
        f"(ratio `{_display(freshness.get('stale_ratio'))}`; threshold `{_display(freshness.get('threshold_days'))}` days)"
    )


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Write a baseline report using the actual pipeline payloads."""
    source_rows = [f"| `{key}` | {_display(value)} |" for key, value in source_summary.items()]
    metric_rows = _metric_rows(metrics) or ["| _none_ | - |"]
    quality_rows = _quality_rows(quality) or ["| _none_ | - |"]
    markdown = "\n".join(
        [
            "# Phase 1 — Baseline Report",
            "",
            "## Source summary",
            "",
            "| Field | Value |",
            "|---|---|",
            *source_rows,
            "",
            "## Evaluation metrics",
            "",
            "| Metric | Value |",
            "|---|---|",
            *metric_rows,
            "",
            "## Data quality",
            "",
            f"Overall status: **{_quality_status(quality)}**; rows: `{_display(quality.get('row_count'))}`.",
            "",
            "| Expectation | Status |",
            "|---|---|",
            *quality_rows,
            "",
            "## Freshness",
            "",
            _freshness_summary(freshness),
            "",
        ]
    )
    write_text(Path(report_path), markdown)


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Write a three-state comparison report for corruption and repair."""
    metric_names = [
        "retrieval_hit_rate",
        "mean_token_f1",
        "judge_accuracy",
        "mean_judge_score",
    ]
    metric_rows = []
    for name in metric_names:
        baseline = baseline_metrics.get(name)
        corrupted = corrupted_metrics.get(name)
        repaired = repaired_metrics.get(name)
        metric_rows.append(
            f"| `{name}` | {_display(baseline)} | {_display(corrupted)} | {_display(repaired)} |"
        )

    quality_rows = [
        f"| Baseline | {_quality_status({'success': True})} | - |",
        f"| Corrupted | {_quality_status(corrupted_quality)} | {_display(corrupted_quality.get('row_count'))} |",
        f"| Repaired | {_quality_status(repaired_quality)} | {_display(repaired_quality.get('row_count'))} |",
    ]
    markdown = "\n".join(
        [
            "# Corruption and Repair Report",
            "",
            "## Executive comparison",
            "",
            "| Metric | Baseline | Corrupted | Repaired |",
            "|---|---:|---:|---:|",
            *metric_rows,
            "",
            "## Quality Gate comparison",
            "",
            "| State | Status | Rows |",
            "|---|---|---:|",
            *quality_rows,
            "",
            "## Freshness comparison",
            "",
            "### Corrupted",
            "",
            _freshness_summary(corrupted_freshness),
            "",
            "### Repaired",
            "",
            _freshness_summary(repaired_freshness),
            "",
            "## Interpretation",
            "",
            "- Corrupted data is expected to violate one or more quality expectations and reduce retrieval/answer metrics.",
            "- Repaired data must be rebuilt from the raw snapshot, not from the corrupted dataframe.",
            "- Compare the repaired metrics with baseline to verify idempotent recovery.",
            "",
        ]
    )
    write_text(Path(report_path), markdown)
