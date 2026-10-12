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
├── docs/
├── reports/
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

Generate sample telemetry data:

```bash
python -m voltguard.simulator --output data/sample_telemetry.csv
```

Start the dashboard:

```bash
python -m streamlit run app.py
```

Open the local URL displayed in the terminal to access the dashboard.

## Run Tests

```bash
python -m pytest -q
```

## Dataset
The project uses synthetic industrial telemetry data for development and testing. The sample dataset is intended for educational and demonstration purposes.

## Project Status
Week 1: Initial project setup and documentation.

Further development, testing, and dashboard improvements will be added progressively.

## Disclaimer
VoltGuard is an educational cybersecurity prototype. Its detection results are intended for demonstration and research, not as a replacement for validated industrial security systems.

## Author
Pradnya Gaikwad
