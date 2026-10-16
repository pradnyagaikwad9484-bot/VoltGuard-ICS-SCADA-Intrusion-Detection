"""Physics-aware and statistical anomaly detection for synthetic telemetry."""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from sklearn.ensemble import IsolationForest

NUMERIC_FEATURES = ["tank_level_pct", "inlet_valve_open", "outlet_valve_open", "inlet_flow_lpm", "outlet_flow_lpm", "pressure_bar", "temperature_c"]


def validate_columns(df: pd.DataFrame) -> None:
    missing = [c for c in NUMERIC_FEATURES if c not in df.columns]
    if missing: raise ValueError(f"Missing required telemetry columns: {', '.join(missing)}")
    if df.empty: raise ValueError("Input telemetry is empty")


def physics_rules(df: pd.DataFrame) -> pd.DataFrame:
    """Return explainable rule flags; thresholds are illustrative only."""
    validate_columns(df); result = df.copy()
    level = pd.to_numeric(result["tank_level_pct"], errors="coerce")
    valve = pd.to_numeric(result["inlet_valve_open"], errors="coerce")
    flow = pd.to_numeric(result["inlet_flow_lpm"], errors="coerce")
    pressure = pd.to_numeric(result["pressure_bar"], errors="coerce")
    result["rule_out_of_range"] = (level < 0) | (level > 100) | (pressure < 0.4) | (pressure > 2.8)
    result["rule_level_jump"] = level.diff().abs() > 12.0
    result["rule_valve_flow_mismatch"] = (valve == 0) & (flow > 4.0)
    result["rule_pressure_spike"] = (pressure - pressure.rolling(10, min_periods=3).median()).abs() > 0.65
    rule_cols = ["rule_out_of_range", "rule_level_jump", "rule_valve_flow_mismatch", "rule_pressure_spike"]
    result["rule_flag_count"] = result[rule_cols].fillna(False).astype(int).sum(axis=1)
    return result


def analyze_telemetry(df: pd.DataFrame, contamination: float = 0.04, seed: int = 42) -> pd.DataFrame:
    ruled = physics_rules(df)
    if not 0.001 <= contamination <= 0.5: raise ValueError("contamination must be between 0.001 and 0.5")
    x = ruled[NUMERIC_FEATURES].apply(pd.to_numeric, errors="coerce")
    x = x.replace([float("inf"), float("-inf")], float("nan"))
    x = x.fillna(x.median()).fillna(0)
    model = IsolationForest(n_estimators=150, contamination=contamination, random_state=seed)
    model.fit(x)
    ruled["statistical_anomaly"] = model.predict(x) == -1
    raw = -model.decision_function(x); lo, hi = float(raw.min()), float(raw.max())
    normalized = (raw - lo) / (hi - lo) if hi > lo else raw * 0
    ruled["statistical_score"] = (normalized * 100).round(1)
    ruled["risk_score"] = (ruled["rule_flag_count"].clip(upper=4) * 20 + ruled["statistical_anomaly"].astype(int) * 20).clip(upper=100).astype(int)
    ruled["severity"] = pd.cut(ruled["risk_score"], bins=[-1, 19, 39, 69, 100], labels=["LOW", "MEDIUM", "HIGH", "CRITICAL"]).astype(str)
    ruled["detected_anomaly"] = (ruled["rule_flag_count"] > 0) | ruled["statistical_anomaly"]
    return ruled


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("input"); parser.add_argument("--output", default="reports/analysis.csv"); parser.add_argument("--contamination", type=float, default=0.04)
    args = parser.parse_args(); df = pd.read_csv(args.input)
    results = analyze_telemetry(df, contamination=args.contamination)
    path = Path(args.output); path.parent.mkdir(parents=True, exist_ok=True); results.to_csv(path, index=False)
    print(f"Analyzed {len(results)} rows; flagged {int(results['detected_anomaly'].sum())}. Output: {path}")

if __name__ == "__main__": main()
