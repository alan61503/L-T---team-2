import sqlite3
import time
import os
from pathlib import Path
from typing import Any, Dict

import joblib
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from live_thingspeak_inference import (
    derive_operational_status,
    estimate_load_thresholds,
    fetch_latest_feed,
    infer_once,
    load_env_file,
    map_thingspeak_to_features,
)

DB_PATH = Path("cloud_events.db")
DEFAULT_MODEL = "stress_model.pkl"
DEFAULT_REFERENCE_DATA = "synthetic_stress_data_3class.csv"
DEFAULT_SIM_CSV = "thingspeak_demo.csv"


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            event_time_utc TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            source_created_at TEXT,
            source_entry_id INTEGER,
            crowd_load REAL,
            temperature REAL,
            pressure REAL,
            prediction_id INTEGER,
            prediction_label TEXT,
            load_level TEXT,
            occupancy_status TEXT,
            risk_score REAL,
            risk_alert TEXT,
            PRIMARY KEY (channel_id, source_entry_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def _get_state(conn: sqlite3.Connection, key: str, default: str = "0") -> str:
    row = conn.execute("SELECT value FROM app_state WHERE key = ?", (key,)).fetchone()
    return row[0] if row else default


def _set_state(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO app_state(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    conn.commit()


def _insert_event(conn: sqlite3.Connection, row: Dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO events(
            event_time_utc, channel_id, source_created_at, source_entry_id,
            crowd_load, temperature, pressure,
            prediction_id, prediction_label,
            load_level, occupancy_status, risk_score, risk_alert
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["event_time_utc"],
            row["channel_id"],
            row.get("source_created_at"),
            row.get("source_entry_id"),
            row.get("crowd_load"),
            row.get("temperature"),
            row.get("pressure"),
            row.get("prediction_id"),
            row.get("prediction_label"),
            row.get("load_level"),
            row.get("occupancy_status"),
            row.get("risk_score"),
            row.get("risk_alert"),
        ),
    )
    conn.commit()


def _latest_event(conn: sqlite3.Connection) -> Dict[str, Any]:
    row = conn.execute(
        "SELECT * FROM events ORDER BY source_entry_id DESC LIMIT 1"
    ).fetchone()
    if row is None:
        return {}

    columns = [d[0] for d in conn.execute("PRAGMA table_info(events)")]
    # PRAGMA returns tuple where column name is index 1.
    col_names = [c[1] for c in conn.execute("PRAGMA table_info(events)")]
    return {k: v for k, v in zip(col_names, row)}


def _read_events(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query(
        "SELECT * FROM events ORDER BY source_entry_id ASC", conn
    )


def _fetch_simulated_feed(conn: sqlite3.Connection, sim_csv: str) -> Dict[str, Any]:
    df = pd.read_csv(sim_csv)
    if df.empty:
        return {}

    idx = int(_get_state(conn, "sim_index", "0"))
    idx = idx % len(df)

    row = df.iloc[idx]
    _set_state(conn, "sim_index", str(idx + 1))

    return {
        "field1": row.get("field1", 0.0),
        "field2": row.get("field2", 0.0),
        "field3": row.get("field3", 0.0),
        "created_at": row.get("created_at", ""),
        "entry_id": int(row.get("entry_id", idx + 1)),
    }


def _status_color(occupancy: str) -> str:
    color_map = {
        "SAFE": "#2e7d32",
        "LIMITED": "#ef6c00",
        "UNSAFE": "#c62828",
    }
    return color_map.get(str(occupancy).upper(), "#455a64")


def main() -> None:
    load_env_file()

    st.set_page_config(page_title="StressNet Cloud Live Dashboard", layout="wide")
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

    st.title("StressNet Cloud Real-Time Dashboard")
    st.caption("Runs live in cloud without Power BI license.")

    model_path = st.sidebar.text_input("Model path", value=os.getenv("MODEL_PATH", DEFAULT_MODEL))
    reference_data = st.sidebar.text_input(
        "Reference data", value=os.getenv("REFERENCE_DATA", DEFAULT_REFERENCE_DATA)
    )
    use_simulation = st.sidebar.toggle(
        "Use simulation CSV", value=_env_bool("USE_SIMULATION", False)
    )
    sim_csv = st.sidebar.text_input("Simulation CSV", value=os.getenv("SIMULATION_CSV", DEFAULT_SIM_CSV))

    conn = _connect_db()

    try:
        bundle = joblib.load(model_path)
        low_mid, mid_high = estimate_load_thresholds(reference_data)
    except Exception as exc:
        st.error(f"Could not load model/reference data: {exc}")
        return

    channel_id = st.secrets.get("THINGSPEAK_CHANNEL_ID", None) if hasattr(st, "secrets") else None
    read_key = st.secrets.get("THINGSPEAK_READ_API_KEY", None) if hasattr(st, "secrets") else None

    if not channel_id:
        channel_id = os.getenv("THINGSPEAK_CHANNEL_ID", "")
    if not read_key:
        read_key = os.getenv("THINGSPEAK_READ_API_KEY", "")

    try:
        if use_simulation:
            feed = _fetch_simulated_feed(conn, sim_csv)
            source_channel = "simulation"
        else:
            if not channel_id or not read_key:
                st.warning("Set THINGSPEAK_CHANNEL_ID and THINGSPEAK_READ_API_KEY in environment/secrets.")
                feed = {}
                source_channel = "n/a"
            else:
                feed = fetch_latest_feed(channel_id, read_key)
                source_channel = str(channel_id)

        if feed:
            incoming = map_thingspeak_to_features(feed)
            result = infer_once(bundle, incoming, reference_data)
            status = derive_operational_status(
                result["prediction_label"],
                incoming["crowd_load"],
                low_mid,
                mid_high,
            )

            row = {
                "event_time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "channel_id": source_channel,
                "source_created_at": feed.get("created_at", ""),
                "source_entry_id": int(feed.get("entry_id", 0) or 0),
                "crowd_load": float(incoming["crowd_load"]),
                "temperature": float(incoming["temperature"]),
                "pressure": float(incoming["pressure"]),
                "prediction_id": int(result["prediction_id"]),
                "prediction_label": str(result["prediction_label"]),
                "load_level": status["load_level"],
                "occupancy_status": status["occupancy_status"],
                "risk_score": float(status["risk_score"]),
                "risk_alert": status["risk_alert"],
            }
            _insert_event(conn, row)
    except Exception as exc:
        st.error(f"Live fetch/inference failed: {exc}")

    events_df = _read_events(conn)
    latest = _latest_event(conn)

    if not latest:
        st.info("No events yet. Check credentials or enable simulation mode in sidebar.")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Current Occupancy", latest.get("occupancy_status", "N/A"))
    c2.metric("Current Load Level", latest.get("load_level", "N/A"))
    c3.metric("Current Risk Score", latest.get("risk_score", "N/A"))

    occupancy = str(latest.get("occupancy_status", "N/A"))
    st.markdown(
        f"<div style='padding:12px;border-radius:8px;background:{_status_color(occupancy)};color:white;'>"
        f"<strong>Active Alert:</strong> {latest.get('risk_alert', 'N/A')}</div>",
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)
    with left:
        st.subheader("Risk Trend")
        if {"source_entry_id", "risk_score"}.issubset(events_df.columns):
            plot_df = events_df[["source_entry_id", "risk_score"]].copy()
            plot_df = plot_df.rename(columns={"source_entry_id": "entry"})
            st.line_chart(plot_df, x="entry", y="risk_score")

    with right:
        st.subheader("Crowd Load Trend")
        if {"source_entry_id", "crowd_load"}.issubset(events_df.columns):
            plot_df = events_df[["source_entry_id", "crowd_load"]].copy()
            plot_df = plot_df.rename(columns={"source_entry_id": "entry"})
            st.line_chart(plot_df, x="entry", y="crowd_load")

    st.subheader("Recent Events")
    shown_cols = [
        "source_entry_id",
        "event_time_utc",
        "prediction_label",
        "load_level",
        "occupancy_status",
        "risk_score",
        "risk_alert",
    ]
    shown = [c for c in shown_cols if c in events_df.columns]
    st.dataframe(events_df[shown].tail(20), use_container_width=True)

    st.caption(f"Last refreshed: {time.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
