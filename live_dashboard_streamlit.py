import time
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

EVENTS_CSV = Path("analytics_output/live_stress_events.csv")
STATUS_CSV = Path("analytics_output/current_status.csv")


def load_csv_safe(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def to_datetime_safe(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def status_color(occupancy: str) -> str:
    color_map = {
        "SAFE": "#2e7d32",
        "LIMITED": "#ef6c00",
        "UNSAFE": "#c62828",
    }
    return color_map.get(str(occupancy).upper(), "#455a64")


def main() -> None:
    st.set_page_config(page_title="StressNet Live Dashboard", layout="wide")

    # Client-side reload keeps dashboard near-real-time without external services.
    refresh_seconds = st.sidebar.slider("Auto-refresh seconds", min_value=2, max_value=30, value=5)
    components.html(
        f"""
        <script>
        setTimeout(function() {{
            window.parent.location.reload();
        }}, {refresh_seconds * 1000});
        </script>
        """,
        height=0,
    )

    st.title("StressNet Live Monitoring Dashboard")
    st.caption("No Power BI Service license required. Data source: local analytics CSV outputs.")

    status_df = load_csv_safe(STATUS_CSV)
    events_df = load_csv_safe(EVENTS_CSV)

    if status_df.empty and events_df.empty:
        st.warning("No analytics data found yet. Run live_thingspeak_inference.py first.")
        st.code("python live_thingspeak_inference.py --simulate-csv thingspeak_demo.csv")
        return

    status_df = to_datetime_safe(status_df, ["event_time_utc", "source_created_at"])
    events_df = to_datetime_safe(events_df, ["event_time_utc", "source_created_at"])

    if not events_df.empty and "source_entry_id" in events_df.columns:
        events_df = events_df.sort_values("source_entry_id")

    if not status_df.empty:
        latest = status_df.iloc[-1].to_dict()
    elif not events_df.empty:
        latest = events_df.iloc[-1].to_dict()
    else:
        latest = {}

    occupancy = str(latest.get("occupancy_status", "N/A"))
    load_level = str(latest.get("load_level", "N/A"))
    risk_score = latest.get("risk_score", "N/A")
    risk_alert = str(latest.get("risk_alert", "N/A"))

    c1, c2, c3 = st.columns(3)
    c1.metric("Current Occupancy", occupancy)
    c2.metric("Current Load Level", load_level)
    c3.metric("Current Risk Score", risk_score)

    st.markdown(
        f"<div style='padding:12px;border-radius:8px;background:{status_color(occupancy)};color:white;'>"
        f"<strong>Active Alert:</strong> {risk_alert}</div>",
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)

    with left:
        st.subheader("Risk Trend")
        if not events_df.empty and {"source_entry_id", "risk_score"}.issubset(events_df.columns):
            risk_plot = events_df[["source_entry_id", "risk_score"]].copy()
            risk_plot = risk_plot.rename(columns={"source_entry_id": "entry"})
            st.line_chart(risk_plot, x="entry", y="risk_score")
        else:
            st.info("Risk trend data not available yet.")

    with right:
        st.subheader("Crowd Load Trend")
        if not events_df.empty and {"source_entry_id", "crowd_load"}.issubset(events_df.columns):
            load_plot = events_df[["source_entry_id", "crowd_load"]].copy()
            load_plot = load_plot.rename(columns={"source_entry_id": "entry"})
            st.line_chart(load_plot, x="entry", y="crowd_load")
        else:
            st.info("Crowd load trend data not available yet.")

    st.subheader("Recent Events")
    wanted_cols = [
        "source_entry_id",
        "event_time_utc",
        "prediction_label",
        "load_level",
        "occupancy_status",
        "risk_score",
        "risk_alert",
    ]
    available = [col for col in wanted_cols if col in events_df.columns]
    if available:
        st.dataframe(events_df[available].tail(20), use_container_width=True)
    else:
        st.info("Event columns not available yet.")

    st.caption(f"Last refreshed: {time.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
