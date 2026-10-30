
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

st.markdown(
    """
<style>
    .block-container {
        padding-top: 1.25rem;
        padding-bottom: 2.5rem;
        max-width: 1500px;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(128,128,128,.22);
    }

    .hero {
        padding: 1.35rem 1.5rem;
        border-radius: 18px;
        margin-bottom: 1rem;
        background: linear-gradient(
            120deg,
            rgba(15,45,75,.98),
            rgba(10,105,115,.94)
        );
        color: white;
        border: 1px solid rgba(255,255,255,.12);
    }

    .hero h1 {
        margin: 0;
        font-size: 2.05rem;
        letter-spacing: -.03em;
    }

    .hero p {
        margin: .45rem 0 0 0;
        color: #d8edf1;
        font-size: 1rem;
    }

    .eyebrow {
        font-size: .75rem;
        text-transform: uppercase;
        letter-spacing: .14em;
        opacity: .82;
    }

    .small-muted {
        font-size: .86rem;
        opacity: .78;
    }

    .metric-card {
        padding: .9rem 1rem;
        border: 1px solid rgba(128,128,128,.25);
        border-radius: 14px;
        min-height: 110px;
    }

    .metric-label {
        font-size: .82rem;
        opacity: .76;
        margin-bottom: .35rem;
    }

    .metric-value {
        font-size: 1.7rem;
        font-weight: 700;
        line-height: 1.2;
    }

    .metric-note {
        font-size: .76rem;
        opacity: .72;
        margin-top: .4rem;
    }

    .section-title {
        font-size: 1.16rem;
        font-weight: 700;
        margin: .3rem 0 .7rem 0;
    }

    .pill {
        display: inline-block;
        padding: .2rem .55rem;
        border-radius: 999px;
        font-size: .75rem;
        font-weight: 650;
        border: 1px solid rgba(128,128,128,.3);
    }

    .footer {
        border-top: 1px solid rgba(128,128,128,.2);
        padding-top: .8rem;
        margin-top: 2rem;
        font-size: .78rem;
        opacity: .7;
    }

    div[data-testid="stMetric"] {
        background: rgba(128,128,128,.055);
        padding: .8rem 1rem;
        border-radius: 12px;
    }

    div[data-testid="stTabs"] button {
        font-weight: 600;
    }
</style>
""",
    unsafe_allow_html=True,
)


def metric_card(label, value, note=""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def prepare_frame(df):
    out = df.copy()

    if "timestamp" in out.columns:
        out["timestamp"] = pd.to_datetime(
            out["timestamp"],
            errors="coerce",
        )

    return out


def make_csv(df):
    return df.to_csv(index=False).encode("utf-8")


def build_summary(results, source_name):
    flagged = results[
        results["detected_anomaly"].fillna(False).astype(bool)
    ]

    severity_counts = {
        str(key): int(value)
        for key, value in results["severity"].fillna("Unknown").value_counts().items()
    }

    return {
        "project": "VoltGuard",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": source_name,
        "dataset_rows": int(len(results)),
        "flagged_rows": int(len(flagged)),
        "normal_rows": int(len(results) - len(flagged)),
        "flag_rate_percent": round(
            float(len(flagged) / max(len(results), 1) * 100),
            2,
        ),
        "severity_counts": severity_counts,
        "limitation": (
            "Educational prototype using synthetic or user-provided telemetry; "
            "not for safety-critical use."
        ),
    }


# ---------------------------- Sidebar ----------------------------

with st.sidebar:
    st.markdown("## 🛡️ VoltGuard")
    st.caption("ICS / SCADA anomaly monitoring")
    st.divider()

    st.markdown("### Data source")

    source_mode = st.radio(
        "Choose input",
        [
            "Generate synthetic data",
            "Upload telemetry CSV",
        ],
        label_visibility="collapsed",
    )

    rows = 1000
    anomaly_rate = 0.04
    contamination = 0.04
    seed = 42
    uploaded = None

    if source_mode == "Generate synthetic data":
        rows = st.slider(
            "Telemetry records",
            200,
            5000,
            1000,
            100,
        )

        anomaly_rate = st.slider(
            "Injected anomaly rate",
            0.01,
            0.20,
            0.04,
            0.01,
        )

        seed = st.number_input(
            "Random seed",
            0,
            999999,
            42,
            1,
        )

    else:
        uploaded = st.file_uploader(
            "Upload CSV",
            type=["csv"],
        )

        st.caption(
            "CSV must contain the required telemetry columns."
        )

    contamination = st.slider(
        "Isolation Forest contamination",
        0.01,
        0.20,
        0.04,
        0.01,
        help=(
            "Expected outlier proportion for the statistical detector; "
            "adjust carefully."
        ),
    )

    run = st.button(
        "▶ Run security analysis",
        type="primary",
        use_container_width=True,
    )

    st.divider()

    st.caption(
        "Prototype only • Synthetic process assumptions"
    )


# ---------------------------- Header ----------------------------

st.markdown(
    """
<div class="hero">
    <div class="eyebrow">
        Industrial Cybersecurity • Defensive Analytics
    </div>
    <h1>VoltGuard</h1>
    <p>
        Physics-aware ICS/SCADA intrusion and process-anomaly detection
    </p>
</div>
""",
    unsafe_allow_html=True,
)

st.warning(
    "Educational prototype: thresholds and process equations are illustrative. "
    "Use synthetic or explicitly authorized data only. "
    "Do not connect this dashboard to production OT/ICS systems."
)


# ---------------------------- Required schema ----------------------------

required = {
    "timestamp",
    "tank_level_pct",
    "inlet_valve_open",
    "outlet_valve_open",
    "inlet_flow_lpm",
    "outlet_flow_lpm",
    "pressure_bar",
    "temperature_c",
}

numeric_columns = [
    "tank_level_pct",
    "inlet_valve_open",
    "outlet_valve_open",
    "inlet_flow_lpm",
    "outlet_flow_lpm",
    "pressure_bar",
    "temperature_c",
]


# ---------------------------- Session state ----------------------------

if "results" not in st.session_state:
    st.session_state.results = None

if "source_name" not in st.session_state:
    st.session_state.source_name = "No dataset loaded"

if "raw_data" not in st.session_state:
    st.session_state.raw_data = None


# ---------------------------- Run analysis ----------------------------

if run:
    try:
        if source_mode == "Upload telemetry CSV":

            if uploaded is None:
                st.error("Upload a CSV file first.")
                st.stop()

            try:
                data = pd.read_csv(uploaded)

            except pd.errors.EmptyDataError:
                st.error(
                    "The uploaded CSV file is empty or has no readable columns."
                )
                st.stop()

            except Exception as exc:
                st.error(f"Could not read the CSV file: {exc}")
                st.stop()

            if data.empty:
                st.error(
                    "The uploaded CSV file contains no data rows."
                )
                st.stop()

            missing = required - set(data.columns)

            if missing:
                st.error(
                    "CSV is missing required columns: "
                    + ", ".join(sorted(missing))
                )
                st.stop()

            data["timestamp"] = pd.to_datetime(
                data["timestamp"],
                errors="coerce",
            )

            if data["timestamp"].isna().any():
                invalid_count = int(
                    data["timestamp"].isna().sum()
                )

                st.error(
                    f"CSV contains {invalid_count} invalid or missing "
                    "timestamp value(s)."
                )
                st.stop()

            for column in numeric_columns:
                data[column] = pd.to_numeric(
                    data[column],
                    errors="coerce",
                )

            invalid_columns = [
                column
                for column in numeric_columns
                if data[column].isna().any()
            ]

            if invalid_columns:
                st.error(
                    "CSV contains invalid or missing numeric values in: "
                    + ", ".join(invalid_columns)
                )
                st.stop()

            infinite_columns = [
                column
                for column in numeric_columns
                if not data[column].map(
                    lambda value: pd.notna(value)
                    and abs(value) != float("inf")
                ).all()
            ]

            if infinite_columns:
                st.error(
                    "CSV contains infinite numeric values in: "
                    + ", ".join(infinite_columns)
                )
                st.stop()

            source_name = uploaded.name

        else:
            data = generate_telemetry(
                int(rows),
                float(anomaly_rate),
                int(seed),
            )

            source_name = (
                f"Synthetic dataset (seed {int(seed)})"
            )

        with st.spinner(
            "Analyzing telemetry and scoring potential anomalies..."
        ):
            results = analyze_telemetry(
                data,
                contamination=float(contamination),
                seed=int(seed),
            )

        st.session_state.results = prepare_frame(results)
        st.session_state.raw_data = prepare_frame(data)
        st.session_state.source_name = source_name

        st.session_state.last_run = datetime.now().strftime(
            "%d %b %Y, %H:%M:%S"
        )

        st.success(
            f"Analysis complete: {len(results):,} telemetry records processed."
        )

    except Exception as exc:
        st.error(f"Analysis failed: {exc}")


# ---------------------------- Main dashboard ----------------------------

results = st.session_state.results


if results is None:

    left, right = st.columns([1.35, 1])

    with left:
        st.markdown("### Security overview")

        st.write(
            "Run the detector on reproducible synthetic telemetry or upload a CSV. "
            "VoltGuard combines transparent process rules with a statistical "
            "outlier detector."
        )

        st.markdown(
            """
            **Detection checks**
            - Tank level and pressure outside illustrative ranges
            - Abrupt tank-level changes
            - Inlet valve / flow mismatch
            - Pressure spikes against a rolling baseline
            - Multivariate outliers using Isolation Forest
            """
        )

    with right:
        st.markdown("### Quick start")

        st.info(
            "1. Choose a data source in the sidebar.\n\n"
            "2. Configure the dataset or upload a CSV.\n\n"
            "3. Click **Run security analysis**."
        )

        st.markdown("### Required CSV columns")

        st.code(
            ", ".join(sorted(required)),
            language="text",
        )


else:
    results = prepare_frame(results)

    flagged = results[
        results["detected_anomaly"].fillna(False).astype(bool)
    ].copy()

    source_name = st.session_state.source_name

    summary = build_summary(
        results,
        source_name,
    )

    # ---------------------------- Top status & metrics ----------------------------

    status = (
        "ATTENTION REQUIRED"
        if len(flagged)
        else "NO ANOMALIES FLAGGED"
    )

    st.markdown(
        f"### Analysis results  <span class='pill'>{status}</span>",
        unsafe_allow_html=True,
    )

    st.caption(
        f"Source: {source_name}  •  "
        f"Last run: {st.session_state.get('last_run', 'Unknown')}"
    )

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        metric_card(
            "TELEMETRY RECORDS",
            f"{len(results):,}",
            "Records analyzed",
        )

    with m2:
        metric_card(
            "FLAGGED RECORDS",
            f"{len(flagged):,}",
            "Rule or statistical signal",
        )

    with m3:
        metric_card(
            "FLAG RATE",
            f"{len(flagged) / max(len(results), 1) * 100:.1f}%",
            "Not a probability of attack",
        )

    with m4:
        critical = int(
            (
                results["severity"].astype(str) == "CRITICAL"
            ).sum()
        )

        metric_card(
            "CRITICAL LABELS",
            f"{critical:,}",
            "Prototype severity scale",
        )

    st.divider()

    tab_overview, tab_events, tab_data, tab_reports, tab_method = st.tabs(
        [
            "📊 Overview",
            "🚨 Flagged events",
            "🧾 Telemetry",
            "⬇ Reports",
            "ℹ Methodology",
        ]
    )


    # ---------------------------- Overview tab ----------------------------

    with tab_overview:

        # Detection overview
        st.markdown("#### Anomaly detection overview")

        total_records = len(results)

        flagged_records = int(
            results["detected_anomaly"]
            .fillna(False)
            .astype(bool)
            .sum()
        )

        normal_records = total_records - flagged_records

        flag_rate = (
            flagged_records / max(total_records, 1) * 100
        )

        gauge_col1, gauge_col2 = st.columns([1, 2])

        with gauge_col1:
            fig, ax = plt.subplots(figsize=(4, 2.8))

            ax.pie(
                [flagged_records, normal_records],
                startangle=90,
                counterclock=False,
                wedgeprops={"width": 0.35},
            )

            ax.text(
                0,
                0,
                f"{flag_rate:.1f}%\nFlagged",
                ha="center",
                va="center",
                fontsize=15,
                fontweight="bold",
            )

            ax.set_title("Anomaly flag rate")

            st.pyplot(
                fig,
                clear_figure=True,
            )

            plt.close(fig)

        with gauge_col2:
            st.metric(
                "Normal records",
                f"{normal_records:,}",
            )

            st.metric(
                "Flagged records",
                f"{flagged_records:,}",
            )

            st.progress(
                min(max(flag_rate / 100, 0.0), 1.0)
            )

            st.caption(
                "Flag rate is a detector output, not an attack probability."
            )

        st.divider()

        chart_left, chart_right = st.columns([1.5, 1])

        with chart_left:
            st.markdown("#### Tank level trend")

            plot_df = results.copy()

            if "timestamp" in plot_df:
                plot_df["timestamp"] = pd.to_datetime(
                    plot_df["timestamp"],
                    errors="coerce",
                )

            fig, ax = plt.subplots(figsize=(10, 4))

            if (
                "timestamp" in plot_df
                and plot_df["timestamp"].notna().any()
            ):
                ax.plot(
                    plot_df["timestamp"],
                    plot_df["tank_level_pct"],
                    linewidth=1.4,
                    label="Tank level",
                )

                points = plot_df[
                    plot_df["detected_anomaly"].fillna(False).astype(bool)
                ]

                if not points.empty:
                    ax.scatter(
                        points["timestamp"],
                        points["tank_level_pct"],
                        s=24,
                        marker="x",
                        label="Flagged",
                    )

                ax.set_xlabel("Timestamp")

            else:
                ax.plot(
                    plot_df["tank_level_pct"].reset_index(drop=True),
                    linewidth=1.4,
                    label="Tank level",
                )

                points = plot_df[
                    plot_df["detected_anomaly"].fillna(False).astype(bool)
                ]

                if not points.empty:
                    ax.scatter(
                        points.index,
                        points["tank_level_pct"],
                        s=24,
                        marker="x",
                        label="Flagged",
                    )

                ax.set_xlabel("Record")

            ax.set_ylabel("Tank level (%)")

            ax.set_title(
                "Process trend with detector flags",
                loc="left",
                fontsize=11,
                pad=10,
            )

            ax.grid(
                True,
                alpha=0.22,
            )

            ax.legend(
                loc="best",
                frameon=True,
            )

            ax.margins(x=0.01)

            fig.tight_layout()

            st.pyplot(
                fig,
                clear_figure=True,
            )

            plt.close(fig)

            # Multi-sensor telemetry visualization
            st.markdown("#### Multi-sensor telemetry trends")

            sensor_columns = [
                "pressure_bar",
                "temperature_c",
                "inlet_flow_lpm",
                "outlet_flow_lpm",
            ]

            available_sensors = [
                column
                for column in sensor_columns
                if column in results.columns
            ]

            if available_sensors:
                selected_sensors = st.multiselect(
                    "Select sensors to visualize",
                    available_sensors,
                    default=available_sensors[:2],
                    key="overview_sensor_selection",
                )

                if selected_sensors:
                    st.line_chart(
                        results[selected_sensors].reset_index(drop=True),
                        use_container_width=True,
                    )
                else:
                    st.info(
                        "Select at least one sensor to display its trend."
                    )

        with chart_right:
            st.markdown("#### Severity distribution")

            severity_order = [
                "LOW",
                "MEDIUM",
                "HIGH",
                "CRITICAL",
            ]

            counts = (
                flagged["severity"]
                .astype(str)
                .value_counts()
                .reindex(
                    severity_order,
                    fill_value=0,
                )
            )

            st.bar_chart(
                counts,
                y_label="Flagged records",
            )

            st.caption(
                "Counts include flagged records only, not all telemetry rows."
            )

            st.markdown("#### Detection signal breakdown")

            signal_cols = [
                column
                for column in [
                    "rule_out_of_range",
                    "rule_level_jump",
                    "rule_valve_flow_mismatch",
                    "rule_pressure_spike",
                    "statistical_anomaly",
                ]
                if column in results.columns
            ]

            if signal_cols:
                signal_counts = (
                    results[signal_cols]
                    .fillna(False)
                    .astype(bool)
                    .sum()
                    .sort_values(ascending=False)
                )

                signal_counts.index = [
                    name.replace("rule_", "")
                    .replace("_", " ")
                    .title()
                    for name in signal_counts.index
                ]

                st.bar_chart(signal_counts)

        st.markdown("#### Highest risk records")

        if "risk_score" in results.columns:
            high_risk = (
                results.sort_values(
                    ["risk_score"],
                    ascending=False,
                )
                .head(10)
            )

            display_cols = [
                column
                for column in [
                    "timestamp",
                    "risk_score",
                    "severity",
                    "rule_flag_count",
                    "statistical_anomaly",
                ]
                if column in high_risk.columns
            ]

            st.dataframe(
                high_risk[display_cols],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("Risk score is not available in this result dataset.")


    # ---------------------------- Flagged events tab ----------------------------

    with tab_events:
        st.markdown("#### Investigate flagged telemetry")

        if flagged.empty:
            st.success(
                "No records were flagged by the current configuration."
            )

        else:
            filter_severity = st.multiselect(
                "Filter by severity",
                [
                    "LOW",
                    "MEDIUM",
                    "HIGH",
                    "CRITICAL",
                ],
                default=[
                    "MEDIUM",
                    "HIGH",
                    "CRITICAL",
                ],
            )

            filtered = flagged[
                flagged["severity"]
                .astype(str)
                .isin(filter_severity)
            ]

            st.caption(
                f"Showing {len(filtered):,} of {len(flagged):,} flagged records."
            )

            event_cols = [
                column
                for column in [
                    "timestamp",
                    "tank_level_pct",
                    "inlet_valve_open",
                    "inlet_flow_lpm",
                    "outlet_flow_lpm",
                    "pressure_bar",
                    "temperature_c",
                    "rule_flag_count",
                    "statistical_anomaly",
                    "risk_score",
                    "severity",
                    "anomaly_type",
                ]
                if column in filtered.columns
            ]

            st.dataframe(
                filtered[event_cols],
                use_container_width=True,
                hide_index=True,
            )

            st.download_button(
                "Download filtered events CSV",
                make_csv(filtered),
                "voltguard_flagged_events.csv",
                "text/csv",
                use_container_width=True,
            )

            if "rule_flag_count" in filtered.columns:
                with st.expander("Explain detection rules"):
                    st.write(
                        "- **Out of range:** level or pressure outside "
                        "the prototype limits."
                    )

                    st.write(
                        "- **Level jump:** absolute change in tank level "
                        "exceeds the illustrative threshold."
                    )

                    st.write(
                        "- **Valve/flow mismatch:** inlet valve is closed "
                        "while inlet flow is unusually high."
                    )

                    st.write(
                        "- **Pressure spike:** pressure differs substantially "
                        "from its rolling median."
                    )

                    st.write(
                        "- **Statistical anomaly:** Isolation Forest marks "
                        "the record as an outlier."
                    )

                    st.caption(
                        "A flagged record is a review signal, "
                        "not proof of malicious activity."
                    )


    # ---------------------------- Telemetry tab ----------------------------

    with tab_data:
        st.markdown("#### Telemetry data")

        search = st.text_input(
            "Search table values (optional)",
            placeholder="e.g. CRITICAL or sensor_spike",
        )

        view = results

        if search:
            mask = (
                view.astype(str)
                .apply(
                    lambda col: col.str.contains(
                        search,
                        case=False,
                        na=False,
                    )
                )
                .any(axis=1)
            )

            view = view[mask]

        st.caption(
            f"{len(view):,} records shown"
        )

        st.dataframe(
            view,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download complete analyzed dataset CSV",
            make_csv(results),
            "voltguard_analysis.csv",
            "text/csv",
            use_container_width=True,
        )


    # ---------------------------- Reports tab ----------------------------

    with tab_reports:
        st.markdown("#### Export results")

        st.write(
            "Download an analysis CSV and a compact JSON summary "
            "for your project documentation."
        )

        st.download_button(
            "⬇ Download analysis CSV",
            make_csv(results),
            "voltguard_analysis.csv",
            "text/csv",
            use_container_width=True,
        )

        st.download_button(
            "⬇ Download summary JSON",
            json.dumps(
                summary,
                indent=2,
            ),
            "voltguard_summary.json",
            "application/json",
            use_container_width=True,
        )

        if st.button(
            "Save reports inside project folder",
            use_container_width=True,
        ):
            try:
                csv_path, json_path = export_reports(results)

                st.success(
                    f"Reports saved to `{csv_path}` and `{json_path}`."
                )

            except Exception as exc:
                st.error(
                    f"Could not save reports: {exc}"
                )

        st.json(summary)


    # ---------------------------- Methodology tab ----------------------------

    with tab_method:
        st.markdown("#### How VoltGuard works")

        st.markdown(
            """
            1. **Input:** synthetic or user-provided telemetry.
            2. **Physics-aware rules:** inspect process values and simple actuator/sensor relationships.
            3. **Statistical detection:** Isolation Forest flags multivariate outliers.
            4. **Risk score:** combines rule flags and the statistical signal using prototype weights.
            5. **Review:** findings are presented for human investigation and exported for documentation.
            """
        )

        st.info(
            "Risk score and severity are heuristic demonstration labels, "
            "not calibrated probabilities or an industry-standard OT risk rating."
        )

        st.markdown("**Required telemetry schema**")

        st.code(
            ", ".join(sorted(required)),
            language="text",
        )

        st.markdown("**Known limitations**")

        st.write(
            "- Synthetic data does not represent all real industrial behavior."
        )

        st.write(
            "- An anomaly can be caused by noise, a fault, a configuration issue, or an attack."
        )

        st.write(
            "- The prototype is not validated for real-world or safety-critical use."
        )


# ---------------------------- Footer ----------------------------

st.markdown(
    """
    <div class='footer'>
        VoltGuard • Defensive educational prototype • Use authorized data only •
        Never use prototype alerts as the sole basis for operational decisions.
    </div>
    """,
    unsafe_allow_html=True,
)
