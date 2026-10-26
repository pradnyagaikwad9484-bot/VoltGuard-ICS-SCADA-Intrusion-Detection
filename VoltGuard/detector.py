"""
Physics-aware and statistical anomaly detection for synthetic telemetry.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.ensemble import IsolationForest


# ---------------------------- Constants ----------------------------

NUMERIC_FEATURES = [
    "tank_level_pct",
    "inlet_valve_open",
    "outlet_valve_open",
    "inlet_flow_lpm",
    "outlet_flow_lpm",
    "pressure_bar",
    "temperature_c",
]

RULE_COLUMNS = [
    "rule_out_of_range",
    "rule_level_jump",
    "rule_valve_flow_mismatch",
    "rule_pressure_spike",
]


# ---------------------------- Input validation ----------------------------

def validate_columns(df: pd.DataFrame) -> None:
    """
    Validate required telemetry columns and input data.

    Raises:
        ValueError: If required columns are missing, the dataframe is empty,
                    or numeric telemetry values are invalid.
    """

    # Check required columns
    missing = [
        column
        for column in NUMERIC_FEATURES
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Missing required telemetry columns: "
            + ", ".join(missing)
        )

    # Check empty dataframe
    if df.empty:
        raise ValueError("Input telemetry is empty")

    # Validate numeric telemetry values
    for column in NUMERIC_FEATURES:

        numeric_values = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        # Detect missing, non-numeric, and infinite values
        invalid_mask = (
            numeric_values.isna()
            | numeric_values.isin(
                [
                    float("inf"),
                    float("-inf"),
                ]
            )
        )

        if invalid_mask.any():

            invalid_count = int(
                invalid_mask.sum()
            )

            raise ValueError(
                f"Column '{column}' contains "
                f"{invalid_count} invalid or missing value(s)"
            )


# ---------------------------- Physics rules ----------------------------

def physics_rules(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return explainable physics-aware rule flags.

    Thresholds are illustrative only.
    """

    validate_columns(df)

    result = df.copy()

    # Convert telemetry features to numeric values
    level = pd.to_numeric(
        result["tank_level_pct"],
        errors="coerce",
    )

    valve = pd.to_numeric(
        result["inlet_valve_open"],
        errors="coerce",
    )

    flow = pd.to_numeric(
        result["inlet_flow_lpm"],
        errors="coerce",
    )

    pressure = pd.to_numeric(
        result["pressure_bar"],
        errors="coerce",
    )

    # Rule 1: Level or pressure outside illustrative limits
    result["rule_out_of_range"] = (
        (level < 0)
        | (level > 100)
        | (pressure < 0.4)
        | (pressure > 2.8)
    )

    # Rule 2: Abrupt tank level change
    result["rule_level_jump"] = (
        level.diff().abs() > 12.0
    )

    # Rule 3: Inlet valve / flow mismatch
    result["rule_valve_flow_mismatch"] = (
        (valve == 0)
        & (flow > 4.0)
    )

    # Rule 4: Pressure spike against rolling median
    rolling_median = pressure.rolling(
        window=10,
        min_periods=3,
    ).median()

    result["rule_pressure_spike"] = (
        (pressure - rolling_median).abs() > 0.65
    )

    # Count rule flags per record
    result["rule_flag_count"] = (
        result[RULE_COLUMNS]
        .fillna(False)
        .astype(int)
        .sum(axis=1)
    )

    return result


# ---------------------------- Statistical detection ----------------------------

def analyze_telemetry(
    df: pd.DataFrame,
    contamination: float = 0.04,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Analyze telemetry using physics-aware rules and Isolation Forest.

    Args:
        df: Input telemetry dataframe.
        contamination: Expected proportion of statistical outliers.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame containing original telemetry and detection results.
    """

    # Validate contamination parameter
    if not 0.001 <= contamination <= 0.5:
        raise ValueError(
            "contamination must be between 0.001 and 0.5"
        )

    # Apply physics-aware rules
    ruled = physics_rules(df)

    # Prepare numeric features
    x = ruled[NUMERIC_FEATURES].apply(
        pd.to_numeric,
        errors="coerce",
    )

    # Replace infinite values with NaN
    x = x.replace(
        [
            float("inf"),
            float("-inf"),
        ],
        float("nan"),
    )

    # Handle remaining missing values
    x = x.fillna(
        x.median()
    ).fillna(0)

    # Initialize Isolation Forest
    model = IsolationForest(
        n_estimators=150,
        contamination=contamination,
        random_state=seed,
    )

    # Fit model
    model.fit(x)

    # Statistical anomaly prediction
    ruled["statistical_anomaly"] = (
        model.predict(x) == -1
    )

    # Calculate statistical anomaly score
    raw_scores = -model.decision_function(x)

    score_min = float(
        raw_scores.min()
    )

    score_max = float(
        raw_scores.max()
    )

    if score_max > score_min:

        normalized_scores = (
            (raw_scores - score_min)
            / (score_max - score_min)
        )

    else:
        normalized_scores = raw_scores * 0

    ruled["statistical_score"] = (
        normalized_scores * 100
    ).round(1)

    # ---------------------------- Risk score ----------------------------

    rule_score = (
        ruled["rule_flag_count"]
        .clip(upper=4)
        * 20
    )

    statistical_score = (
        ruled["statistical_anomaly"]
        .astype(int)
        * 20
    )

    ruled["risk_score"] = (
        rule_score + statistical_score
    ).clip(
        upper=100
    ).astype(int)

    # ---------------------------- Severity ----------------------------

    ruled["severity"] = pd.cut(
        ruled["risk_score"],
        bins=[
            -1,
            19,
            39,
            69,
            100,
        ],
        labels=[
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL",
        ],
    ).astype(str)

    # ---------------------------- Final anomaly flag ----------------------------

    ruled["detected_anomaly"] = (
        (ruled["rule_flag_count"] > 0)
        | ruled["statistical_anomaly"]
    )

    return ruled


# ---------------------------- Command-line interface ----------------------------

def main() -> None:
    """
    Run telemetry analysis from the command line.
    """

    parser = argparse.ArgumentParser(
        description=__doc__
    )

    parser.add_argument(
        "input",
        help="Path to input telemetry CSV file",
    )

    parser.add_argument(
        "--output",
        default="reports/analysis.csv",
        help="Path to save the analysis CSV",
    )

    parser.add_argument(
        "--contamination",
        type=float,
        default=0.04,
        help="Isolation Forest contamination value",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )

    args = parser.parse_args()

    # Read input CSV
    df = pd.read_csv(args.input)

    # Analyze telemetry
    results = analyze_telemetry(
        df,
        contamination=args.contamination,
        seed=args.seed,
    )

    # Prepare output path
    output_path = Path(args.output)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Save analysis output
    results.to_csv(
        output_path,
        index=False,
    )

    # Print summary
    flagged_count = int(
        results["detected_anomaly"].sum()
    )

    print(
        f"Analyzed {len(results)} rows; "
        f"flagged {flagged_count}. "
        f"Output: {output_path}"
    )


# ---------------------------- Entry point ----------------------------

if __name__ == "__main__":
    main()
