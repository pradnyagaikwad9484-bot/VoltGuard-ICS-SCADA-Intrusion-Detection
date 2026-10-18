"""Generate reproducible synthetic water-tank process telemetry."""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd


def generate_telemetry(rows: int = 1000, anomaly_rate: float = 0.04, seed: int = 42) -> pd.DataFrame:
    """Create synthetic telemetry. Values are illustrative, not real plant data."""
    if rows < 10:
        raise ValueError("rows must be at least 10")
    if not 0 <= anomaly_rate <= 0.5:
        raise ValueError("anomaly_rate must be between 0 and 0.5")
    rng = np.random.default_rng(seed)
    timestamps = pd.date_range("2026-01-01", periods=rows, freq="min")
    inlet = rng.choice([0, 1], size=rows, p=[0.35, 0.65]).astype(int)
    outlet = rng.choice([0, 1], size=rows, p=[0.25, 0.75]).astype(int)
    inlet_flow = np.clip(inlet * rng.normal(7.0, 0.8, rows), 0, None)
    outlet_flow = np.clip(outlet * rng.normal(5.0, 0.7, rows), 0, None)
    pressure = np.clip(1.2 + inlet_flow * 0.035 + rng.normal(0, 0.04, rows), 0.5, 2.5)
    temperature = 22 + 0.15 * inlet_flow + rng.normal(0, 0.35, rows)
    level = np.zeros(rows, dtype=float)
    level[0] = 50
    for i in range(1, rows):
        level[i] = np.clip(level[i-1] + 0.16 * (inlet_flow[i] - outlet_flow[i]) + rng.normal(0, 0.12), 0, 100)
    df = pd.DataFrame({
        "timestamp": timestamps, "tank_level_pct": np.round(level, 3),
        "inlet_valve_open": inlet, "outlet_valve_open": outlet,
        "inlet_flow_lpm": np.round(inlet_flow, 3), "outlet_flow_lpm": np.round(outlet_flow, 3),
        "pressure_bar": np.round(pressure, 3), "temperature_c": np.round(temperature, 3),
        "injected_anomaly": False, "anomaly_type": "normal"
    })
    count = int(rows * anomaly_rate)
    if count:
        chosen = rng.choice(np.arange(2, rows), size=min(count, rows-2), replace=False)
        for idx in chosen:
            kind = str(rng.choice(["sensor_spike", "actuator_mismatch", "level_jump", "out_of_range"]))
            df.loc[idx, "injected_anomaly"] = True
            df.loc[idx, "anomaly_type"] = kind
            if kind == "sensor_spike":
                df.loc[idx, "pressure_bar"] = round(float(df.loc[idx, "pressure_bar"] + rng.choice([-1, 1]) * rng.uniform(0.8, 1.5)), 3)
            elif kind == "actuator_mismatch":
                df.loc[idx, "inlet_valve_open"] = 0
                df.loc[idx, "inlet_flow_lpm"] = round(float(rng.uniform(5.5, 9.5)), 3)
            elif kind == "level_jump":
                df.loc[idx, "tank_level_pct"] = round(float(np.clip(df.loc[idx-1, "tank_level_pct"] + rng.choice([-1, 1]) * rng.uniform(18, 35), 0, 100)), 3)
            else:
                df.loc[idx, "tank_level_pct"] = round(float(rng.choice([-8, 108])), 3)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="data/sample_telemetry.csv")
    parser.add_argument("--rows", type=int, default=1000)
    parser.add_argument("--anomaly-rate", type=float, default=0.04)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    df = generate_telemetry(args.rows, args.anomaly_rate, args.seed)
    path = Path(args.output); path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"Wrote {len(df)} synthetic rows to {path}")

if __name__ == "__main__":
    main()
