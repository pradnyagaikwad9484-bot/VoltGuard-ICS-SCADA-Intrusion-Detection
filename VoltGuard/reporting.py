"""Export VoltGuard findings as CSV and JSON."""
import json
from pathlib import Path
import pandas as pd


def export_reports(results: pd.DataFrame, output_dir: str | Path = "reports") -> tuple[Path, Path]:
    output = Path(output_dir); output.mkdir(parents=True, exist_ok=True)
    csv_path = output / "voltguard_findings.csv"; json_path = output / "voltguard_summary.json"
    results.to_csv(csv_path, index=False)
    flagged = results[results["detected_anomaly"] == True]
    summary = {"project": "VoltGuard", "dataset_rows": int(len(results)), "flagged_rows": int(len(flagged)),
               "severity_counts": {str(k): int(v) for k, v in results["severity"].value_counts().items()},
               "limitation": "Synthetic-data educational prototype; not for operational safety decisions."}
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return csv_path, json_path
