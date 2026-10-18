# VoltGuard: Physics-Aware ICS/SCADA Intrusion Detection System

## Project Overview

VoltGuard is a cybersecurity project designed to detect suspicious activities and abnormal behavior in Industrial Control Systems (ICS) and Supervisory Control and Data Acquisition (SCADA) environments.

The project uses simulated industrial telemetry data and physics-aware detection logic to identify potentially abnormal events and help improve industrial system security monitoring.

## Objectives

- Simulate industrial telemetry data for testing.
- Detect suspicious or abnormal system behavior.
- Analyze telemetry data using detection rules.
- Visualize security events through an interactive dashboard.
- Generate reports to support security analysis.

## Key Features

- Synthetic telemetry data generation.
- Physics-aware anomaly detection.
- Interactive Streamlit dashboard.
- CSV data upload and analysis.
- Security event severity visualization.
- CSV and JSON report generation.
- Automated project tests.

## Technologies Used

- Python
- Streamlit
- Pandas
- NumPy
- Plotly
- Pytest

## Project Structure

```text
VoltGuard-Full-Project/
├── app.py
├── README.md
├── requirements.txt
├── data/
│   └── sample_telemetry.csv
├── docs/
│   ├── PROJECT_REPORT.md
│   └── WEEKLY_LOG_TEMPLATE.md
├── reports/
│   └── .gitkeep
├── tests/
│   └── test_voltguard.py
└── voltguard/
    ├── __init__.py
    ├── detector.py
    ├── reporting.py
    └── simulator.py
```

## Installation and Setup

1. Install Python on your computer.
2. Download or clone this repository.
3. Open a terminal in the project folder.
4. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Run the Project

### Generate Sample Telemetry Data

```bash
python -m voltguard.simulator --output data/sample_telemetry.csv
```

### Start the Dashboard

```bash
python -m streamlit run app.py
```

Open the local URL displayed in the terminal to access the dashboard.

## Run Tests

Run the following command from the project folder:

```bash
python -m pytest -q
```

Review the test output to confirm whether all tests pass.

## Dataset

The project uses synthetic industrial telemetry data for development and testing. The sample dataset is intended for educational and demonstration purposes.

## Reporting

VoltGuard includes a reporting module intended to support the generation of CSV and JSON reports for security analysis.

The `reports/` directory is included in the repository for storing generated reports.

## Project Status

- [x] **Week 1:** Initial project setup and documentation.
- [x] **Week 2:** Synthetic telemetry data generation and intrusion detection logic.
- [x] **Week 3:** Streamlit dashboard development.
- [x] **Week 4:** Reporting module, automated test file, and project documentation added.

The project repository contains the main application, telemetry simulator, detection logic, reporting module, sample dataset, dashboard, and automated test file.

**Note:** The presence of the automated test file does not by itself confirm that all tests pass. Run the test command to verify the results.

## Disclaimer

VoltGuard is an educational cybersecurity prototype. Its detection results are intended for demonstration and research, not as a replacement for validated industrial security systems.

## Author

Pradnya Gaikwad
