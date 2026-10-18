import pandas as pd
import pytest
from voltguard.simulator import generate_telemetry
from voltguard.detector import physics_rules, analyze_telemetry
from voltguard.reporting import export_reports


def test_simulator_is_reproducible():
    pd.testing.assert_frame_equal(generate_telemetry(100, .05, 7), generate_telemetry(100, .05, 7))


def test_simulator_row_count():
    assert len(generate_telemetry(120, .02, 1)) == 120


def test_simulator_rejects_too_few_rows():
    with pytest.raises(ValueError): generate_telemetry(5)


def test_simulator_rejects_bad_anomaly_rate():
    with pytest.raises(ValueError): generate_telemetry(100, .9)


def test_physics_rule_flags_out_of_range():
    df = generate_telemetry(50, 0, 2); df.loc[10, "tank_level_pct"] = 120
    assert bool(physics_rules(df).loc[10, "rule_out_of_range"])


def test_physics_rule_flags_valve_flow_mismatch():
    df = generate_telemetry(50, 0, 2); df.loc[10, "inlet_valve_open"] = 0; df.loc[10, "inlet_flow_lpm"] = 8
    assert bool(physics_rules(df).loc[10, "rule_valve_flow_mismatch"])


def test_analysis_has_risk_and_severity():
    result = analyze_telemetry(generate_telemetry(120, .05, 3), seed=3)
    assert result["risk_score"].between(0, 100).all()
    assert set(result["severity"].unique()).issubset({"LOW", "MEDIUM", "HIGH", "CRITICAL"})


def test_report_export_creates_files(tmp_path):
    result = analyze_telemetry(generate_telemetry(80, .05, 4), seed=4)
    csv_path, json_path = export_reports(result, tmp_path)
    assert csv_path.exists() and json_path.exists()
