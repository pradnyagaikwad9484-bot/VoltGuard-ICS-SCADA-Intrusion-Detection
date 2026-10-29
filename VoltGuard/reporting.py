
"""Export VoltGuard findings as validated CSV and JSON reports."""

import json
from pathlib import Path

import pandas as pd


def export_reports(
    results: pd.DataFrame,
    output_dir: str | Path = "reports",
) -> tuple[Path, Path]:
    """Export detailed findings to CSV and a summary to JSON."""
    if not isinstance(results, pd.DataFrame):
        raise TypeError("results must be a pandas DataFrame.")

    required_columns = {"detected_anomaly", "severity"}
    missing_columns = required_columns - set(results.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns: {missing}")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    csv_path = output / "voltguard_findings.csv"
    json_path = output / "voltguard_summary.json"

    results.to_csv(csv_path, index=False)

    flagged = results["detected_anomaly"].eq(True)
    severity = (
        results["severity"]
        .fillna("Unknown")
        .astype(str)
        .replace("", "Unknown")
    )

    summary = {
        "project": "VoltGuard",
        "dataset_rows": int(len(results)),
        "flagged_rows": int(flagged.sum()),
        "normal_rows": int(len(results) - flagged.sum()),
        "severity_counts": {
            str(level): int(count)
            for level, count in severity.value_counts().items()
        },
        "limitation": (
            "Synthetic-data educational prototype; "
            "not for operational safety decisions."
        ),
    }

    json_path.write_text(
        json.dumps(summary, indent=2, allow_nan=False),
        encoding="utf-8",
    )

    return csv_path, json_path
