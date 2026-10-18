# VoltGuard Project Report

## Abstract
VoltGuard is an educational prototype demonstrating a physics-aware approach to detecting unusual behavior in synthetic ICS/SCADA telemetry. It combines rule-based checks for a simplified tank process with a multivariate Isolation Forest detector. Findings are summarized with a transparent risk score and displayed in a Streamlit dashboard.

## Problem statement
Industrial control systems use sensors and actuators to manage physical processes. Network-only monitoring may miss process inconsistencies, while sensor readings can be noisy. This project explores combining simplified process expectations with statistical anomaly detection to flag records for human review.

## Objectives
- Generate repeatable synthetic telemetry for a simplified water tank.
- Detect out-of-range level/pressure values, abrupt level changes, and inlet valve/flow mismatches.
- Compare rule-based indicators with statistical outliers.
- Provide an explainable risk score and exportable findings.

## Scope and assumptions
The project uses synthetic data and a simplified tank balance. Thresholds are illustrative. It does not ingest live PLC data, decode industrial protocols, identify a specific attack family, or guarantee detection of real intrusions.

## Methodology
1. Generate minute-by-minute synthetic process telemetry.
2. Add labeled synthetic examples of sensor spikes, actuator mismatch, level jumps, and out-of-range readings.
3. Apply rule-based checks.
4. Fit Isolation Forest to numeric telemetry and mark statistical outliers.
5. Combine rule count and statistical flags into a risk score.
6. Visualize trends and download results.

## Risk scoring
The prototype adds 20 points per physics rule flag (up to four flags) and 20 points for a statistical anomaly, capped at 100. Severity bins are LOW (0–19), MEDIUM (20–39), HIGH (40–69), and CRITICAL (70–100). These are demonstration settings, not operational risk standards.

## Validation
The included pytest suite covers reproducible simulation, input validation, rule behavior, risk-score bounds, severity labels, and report export. Run `pytest -q` and record the actual output. Do not report tests as passed until run in your environment.

## Limitations
- Synthetic data may not represent real industrial distributions.
- A statistical outlier is not necessarily malicious.
- Thresholds and simplified process dynamics require domain-expert validation.
- The score is illustrative and not calibrated against real incidents.
- Do not connect the prototype to production OT or use it for safety-critical decisions.

## Future work
Evaluate against an authorized documented ICS dataset; add temporal windows and sensor-quality handling; measure precision, recall, false-positive rate, and detection delay using ground-truth labels; calibrate thresholds with an OT/controls expert; and add data lineage and model/version metadata to reports.

## Conclusion
VoltGuard demonstrates how process-aware rules and statistical anomaly detection can be combined in a small defensive prototype. Results are educational signals requiring human investigation, not proof of an intrusion.
