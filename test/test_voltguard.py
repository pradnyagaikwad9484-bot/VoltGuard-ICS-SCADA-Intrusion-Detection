
import json

import pandas as pd
import pytest

from voltguard.simulator import generate_telemetry
from voltguard.detector import physics_rules, analyze_telemetry
from voltguard.reporting import export_reports


# -------------------------
# Simulator tests
# -------------------------

def test_simulator_is_reproducible():
    first = generate_telemetry(100, 0.05, 7)
    second = generate_telemetry(100, 0.05, 7)

    pd.testing.assert_frame_equal(first, second)


def test_simulator_row_count():
    result = generate_telemetry(120, 0.02, 1)

    assert len(result) == 120


def test_simulator_rejects_too_few_rows():
    with pytest.raises(ValueError):
        generate_telemetry(5)


def test_simulator_rejects_bad_anomaly_rate():
    with pytest.raises(ValueError):
        generate_telemetry(100, 0.9)


# -------------------------
# Physics rule tests
# -------------------------

def test_physics_rule_flags_out_of_range():
    df = generate_telemetry(50, 0, 2)
    df.loc[10, "tank_level_pct"] = 120

    result = physics_rules(df)

    assert bool(result.loc[10, "rule_out_of_range"])


def test_physics_rule_flags_valve_flow_mismatch():
    df = generate_telemetry(50, 0, 2)
    df.loc[10, "inlet_valve_open"] = 0
    df.loc[10, "inlet_flow_lpm"] = 8

    result = physics_rules(df)

    assert bool(result.loc[10, "rule_valve_flow_mismatch"])


# -------------------------
# Detector input validation tests
# -------------------------

def test_detector_rejects_missing_required_column():
    df = generate_telemetry(50, 0, 2)
    df = df.drop(columns=["pressure_bar"])

    with pytest.raises(ValueError):
        physics_rules(df)


def test_detector_rejects_non_numeric_telemetry():
    df = generate_telemetry(50, 0, 2)
    df["pressure_bar"] = df["pressure_bar"].astype(object)
    df.loc[10, "pressure_bar"] = "invalid"

    with pytest.raises(ValueError):
        physics_rules(df)


def test_detector_rejects_infinite_telemetry():
    df = generate_telemetry(50, 0, 2)
    df.loc[10, "pressure_bar"] = float("inf")

    with pytest.raises(ValueError):
        physics_rules(df)


def test_detector_rejects_empty_dataframe():
    df = generate_telemetry(50, 0, 2).iloc[0:0].copy()

    with pytest.raises(ValueError):
        physics_rules(df)


# -------------------------
# Analysis tests
# -------------------------

def test_analysis_has_risk_and_severity():
    result = analyze_telemetry(
        generate_telemetry(120, 0.05, 3),
        seed=3,
    )

    assert result["risk_score"].between(0, 100).all()
    assert set(result["severity"].unique()).issubset(
        {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    )


# -------------------------
# Report export tests
# -------------------------

def test_report_export_creates_files(tmp_path):
    result = analyze_telemetry(
        generate_telemetry(80, 0.05, 4),
        seed=4,
    )

    csv_path, json_path = export_reports(result, tmp_path)

    assert csv_path.exists()
    assert json_path.exists()


def test_report_export_creates_valid_json(tmp_path):
    result = analyze_telemetry(
        generate_telemetry(80, 0.05, 4),
        seed=4,
    )

    csv_path, json_path = export_reports(result, tmp_path)

    assert csv_path.exists()
    assert json_path.exists()

    with json_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert data is not None
