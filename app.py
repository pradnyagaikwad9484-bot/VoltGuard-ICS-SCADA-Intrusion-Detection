                "rule_pressure_spike", "statistical_anomaly"
            ] if c in results.columns]
            if signal_cols:
                signal_counts = results[signal_cols].fillna(False).astype(bool).sum().sort_values(ascending=False)
                signal_counts.index = [name.replace("rule_", "").replace("_", " ").title() for name in signal_counts.index]
                st.bar_chart(signal_counts)

        st.markdown("#### Highest risk records")
        high_risk = results.sort_values(["risk_score"], ascending=False).head(10)
        display_cols = [c for c in ["timestamp", "risk_score", "severity", "rule_flag_count", "statistical_anomaly"] if c in high_risk.columns]
        st.dataframe(high_risk[display_cols], use_container_width=True, hide_index=True)

    with tab_events:
        st.markdown("#### Investigate flagged telemetry")
        if flagged.empty:
            st.success("No records were flagged by the current configuration.")
        else:
            filter_severity = st.multiselect(
                "Filter by severity",
                ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                default=["MEDIUM", "HIGH", "CRITICAL"],
            )
            filtered = flagged[flagged["severity"].astype(str).isin(filter_severity)]
            st.caption(f"Showing {len(filtered):,} of {len(flagged):,} flagged records.")
            event_cols = [c for c in [
                "timestamp", "tank_level_pct", "inlet_valve_open", "inlet_flow_lpm",
                "outlet_flow_lpm", "pressure_bar", "temperature_c", "rule_flag_count",
                "statistical_anomaly", "risk_score", "severity", "anomaly_type"
            ] if c in filtered.columns]
            st.dataframe(filtered[event_cols], use_container_width=True, hide_index=True)
            st.download_button(
                "Download filtered events CSV",
                make_csv(filtered),
                "voltguard_flagged_events.csv",
                "text/csv",
                use_container_width=True,
            )
            if "rule_flag_count" in filtered.columns:
                with st.expander("Explain detection rules"):
                    st.write("- **Out of range:** level or pressure outside the prototype limits.")
                    st.write("- **Level jump:** absolute change in tank level exceeds the illustrative threshold.")
                    st.write("- **Valve/flow mismatch:** inlet valve is closed while inlet flow is unusually high.")
                    st.write("- **Pressure spike:** pressure differs substantially from its rolling median.")
                    st.write("- **Statistical anomaly:** Isolation Forest marks the record as an outlier.")
                    st.caption("A flagged record is a review signal, not proof of malicious activity.")

    with tab_data:
        st.markdown("#### Telemetry data")
        search = st.text_input("Search table values (optional)", placeholder="e.g. CRITICAL or sensor_spike")
        view = results
        if search:
            mask = view.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
            view = view[mask]
        st.caption(f"{len(view):,} records shown")
        st.dataframe(view, use_container_width=True, hide_index=True)
        st.download_button(
            "Download complete analyzed dataset CSV",
            make_csv(results),
            "voltguard_analysis.csv",
            "text/csv",
            use_container_width=True,
        )

    with tab_reports:
        st.markdown("#### Export results")
        st.write("Download an analysis CSV and a compact JSON summary for your project documentation.")
        st.download_button(
            "⬇ Download analysis CSV",
            make_csv(results),
            "voltguard_analysis.csv",
            "text/csv",
            use_container_width=True,
        )
        st.download_button(
            "⬇ Download summary JSON",
            json.dumps(summary, indent=2),
            "voltguard_summary.json",
            "application/json",
            use_container_width=True,
        )
        if st.button("Save reports inside project folder", use_container_width=True):
            try:
                csv_path, json_path = export_reports(results)
                st.success(f"Reports saved to `{csv_path}` and `{json_path}`.")
            except Exception as exc:
                st.error(f"Could not save reports: {exc}")
        st.json(summary)

    with tab_method:
        st.markdown("#### How VoltGuard works")
        st.markdown("""
        1. **Input:** synthetic or user-provided telemetry.
        2. **Physics-aware rules:** inspect process values and simple actuator/sensor relationships.
        3. **Statistical detection:** Isolation Forest flags multivariate outliers.
        4. **Risk score:** combines rule flags and the statistical signal using prototype weights.
        5. **Review:** findings are presented for human investigation and exported for documentation.
        """)
        st.info(
            "Risk score and severity are heuristic demonstration labels, not calibrated probabilities "
            "or an industry-standard OT risk rating."
        )
        st.markdown("**Required telemetry schema**")
        st.code(", ".join(sorted(required)), language="text")
        st.markdown("**Known limitations**")
        st.write("- Synthetic data does not represent all real industrial behavior.")
        st.write("- An anomaly can be caused by noise, a fault, a configuration issue, or an attack.")
        st.write("- The prototype is not validated for real-world or safety-critical use.")

st.markdown(
    "<div class='footer'>VoltGuard • Defensive educational prototype • Use authorized data only • "
    "Never use prototype alerts as the sole basis for operational decisions.</div>",
    unsafe_allow_html=True,
)
