import json
from datetime import datetime
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from voltguard.simulator import generate_telemetry
from voltguard.detector import analyze_telemetry
from voltguard.reporting import export_reports

st.set_page_config(
    page_title="VoltGuard | ICS/SCADA Security",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------- Theme & helpers ----------------------------
st.markdown("""
<style>
    .block-container {padding-top: 1.25rem; padding-bottom: 2.5rem; max-width: 1500px;}
    [data-testid="stSidebar"] {border-right: 1px solid rgba(128,128,128,.22);}
    .hero {
        padding: 1.35rem 1.5rem; border-radius: 18px; margin-bottom: 1rem;
        background: linear-gradient(120deg, rgba(15,45,75,.98), rgba(10,105,115,.94));
        color: white; border: 1px solid rgba(255,255,255,.12);
    }
    .hero h1 {margin: 0; font-size: 2.05rem; letter-spacing: -.03em;}
    .hero p {margin: .45rem 0 0 0; color: #d8edf1; font-size: 1rem;}
    .eyebrow {font-size: .75rem; text-transform: uppercase; letter-spacing: .14em; opacity: .82;}
    .small-muted {font-size: .86rem; opacity: .78;}
    .metric-card {
        padding: .9rem 1rem; border: 1px solid rgba(128,128,128,.25);
        border-radius: 14px; min-height: 110px;
    }
    .metric-label {font-size: .82rem; opacity: .76; margin-bottom: .35rem;}
    .metric-value {font-size: 1.7rem; font-weight: 700; line-height: 1.2;}
    .metric-note {font-size: .76rem; opacity: .72; margin-top: .4rem;}
    .section-title {font-size: 1.16rem; font-weight: 700; margin: .3rem 0 .7rem 0;}
    .pill {
        display:inline-block; padding:.2rem .55rem; border-radius:999px;
        font-size:.75rem; font-weight:650; border:1px solid rgba(128,128,128,.3);
    }
    .footer {border-top:1px solid rgba(128,128,128,.2); padding-top: .8rem; margin-top: 2rem; font-size:.78rem; opacity:.7;}
    div[data-testid="stMetric"] {background: rgba(128,128,128,.055); padding: .8rem 1rem; border-radius: 12px;}
    div[data-testid="stTabs"] button {font-weight: 600;}
</style>
""", unsafe_allow_html=True)

def metric_card(label, value, note=""):
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
        unsafe_allow_html=True,
    )

def prepare_frame(df):
    out = df.copy()
    if "timestamp" in out.columns:
        out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")
    return out

def make_csv(df):
    return df.to_csv(index=False).encode("utf-8")

def build_summary(results, source_name):
    flagged = results[results["detected_anomaly"].astype(bool)]
    severity_counts = {str(k): int(v) for k, v in results["severity"].value_counts().items()}
    return {
        "project": "VoltGuard",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": source_name,
        "dataset_rows": int(len(results)),
        "flagged_rows": int(len(flagged)),
        "flag_rate_percent": round(float(len(flagged) / max(len(results), 1) * 100), 2),
        "severity_counts": severity_counts,
        "limitation": "Educational prototype using synthetic or user-provided telemetry; not for safety-critical use."
    }

# ---------------------------- Sidebar ----------------------------
with st.sidebar:
    st.markdown("## 🛡️ VoltGuard")
    st.caption("ICS / SCADA anomaly monitoring")
    st.divider()
    st.markdown("### Data source")
    source_mode = st.radio(
        "Choose input",
        ["Generate synthetic data", "Upload telemetry CSV"],
        label_visibility="collapsed",
    )

    rows, anomaly_rate, contamination, seed = 1000, 0.04, 0.04, 42
    uploaded = None
    if source_mode == "Generate synthetic data":
        rows = st.slider("Telemetry records", 200, 5000, 1000, 100)
        anomaly_rate = st.slider("Injected anomaly rate", 0.01, 0.20, 0.04, 0.01)
