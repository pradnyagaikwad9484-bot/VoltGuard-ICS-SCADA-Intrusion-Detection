"""Export VoltGuard findings as validated CSV and JSON reports."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd


def export_reports(
    results: pd.DataFrame,
    output_dir: str | Path = "reports",
) -> tuple[Path, Path]:
    """Export detailed VoltGuard findings to CSV and JSON summary reports."""

    # Validate input type
    if not isinstance(results, pd.DataFrame):
        raise TypeError("results must be a pandas DataFrame.")

    # Validate required analysis columns
    required_columns = {"detected_anomaly", "severity"}
    missing_columns = required_columns - set(results.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns: {missing}")

    # Create output directory if needed
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    # Report file paths
    csv_path = output / "voltguard_findings.csv"
    json_path = output / "voltguard_summary.json"

    # Export complete analysis results
    results.to_csv(csv_path, index=False)

    # Calculate anomaly statistics
    anomaly_flags = results["detected_anomaly"].fillna(False).astype(bool)

    total_rows = len(results)
    flagged_rows = int(anomaly_flags.sum())
    normal_rows = int(total_rows - flagged_rows)

    flag_rate_percent = round(
        (flagged_rows / max(total_rows, 1)) * 100,
        2,
    )

    # Clean severity values
    severity = (
        results["severity"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
        .replace("", "Unknown")
    )

    severity_counts = {
        str(level): int(count)
        for level, count in severity.value_counts().items()
    }

    # Optional risk statistics
    risk_summary = {}

    if "risk_score" in results.columns:
        risk_scores = pd.to_numeric(
            results["risk_score"],
            errors="coerce",
        )

        valid_scores = risk_scores.dropna()

        if not valid_scores.empty:
            risk_summary = {
                "average_risk_score": round(
                    float(valid_scores.mean()),
                    2,
                ),
                "maximum_risk_score": round(
                    float(valid_scores.max()),
                    2,
                ),
                "minimum_risk_score": round(
                    float(valid_scores.min()),
                    2,
                ),
            }

    # Build JSON summary
    summary = {
        "project": "VoltGuard",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "dataset_rows": int(total_rows),
        "flagged_rows": flagged_rows,
        "normal_rows": normal_rows,
        "flag_rate_percent": flag_rate_percent,
        "severity_counts": severity_counts,
        "risk_summary": risk_summary,
        "reports": {
            "findings_csv": str(csv_path),
            "summary_json": str(json_path),
        },
        "limitation": (
            "VoltGuard is an educational defensive cybersecurity prototype. "
            "Synthetic telemetry and prototype detection scores must not be "
            "used as the sole basis for operational or safety-critical decisions."
        ),
    }

    # Write JSON report
    json_path.write_text(
        json.dumps(
            summary,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ),
        encoding="utf-8",
    )

    return csv_path, json_path
