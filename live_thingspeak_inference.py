import argparse
import csv
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import joblib
import pandas as pd


ANALYTICS_FIELDS = [
    "event_time_utc",
    "channel_id",
    "source_created_at",
    "source_entry_id",
    "crowd_load",
    "temperature",
    "pressure",
    "prediction_id",
    "prediction_label",
    "load_level",
    "occupancy_status",
    "risk_score",
    "risk_alert",
    "write_back_enabled",
    "write_back_response",
]


def load_env_file(path: str = ".env") -> None:
    # Lightweight .env loader so users can run without extra dependencies.
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def append_analytics_row(output_path: str, row: Dict[str, Any]) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ANALYTICS_FIELDS)
        if (not file_exists) or path.stat().st_size == 0:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in ANALYTICS_FIELDS})


def write_status_snapshot(output_path: str, row: Dict[str, Any]) -> None:
    # Single-row status file is convenient for Power BI card visuals.
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ANALYTICS_FIELDS)
        writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in ANALYTICS_FIELDS})


def load_level_from_thresholds(
    crowd_load: float, low_to_medium_threshold: float, medium_to_high_threshold: float
) -> str:
    if crowd_load < low_to_medium_threshold:
        return "Low"
    if crowd_load < medium_to_high_threshold:
        return "Medium"
    return "High"


def estimate_load_thresholds(reference_csv: str) -> Tuple[float, float]:
    try:
        df = pd.read_csv(reference_csv)
        load_col = "crowd_load" if "crowd_load" in df.columns else "force"
        if load_col not in df.columns:
            return 150.0, 350.0

        series = pd.to_numeric(df[load_col], errors="coerce").dropna()
        if series.empty:
            return 150.0, 350.0

        return float(series.quantile(0.33)), float(series.quantile(0.66))
    except Exception:
        return 150.0, 350.0


def derive_operational_status(
    prediction_label: str,
    crowd_load: float,
    low_to_medium_threshold: float,
    medium_to_high_threshold: float,
) -> Dict[str, Any]:
    load_level = load_level_from_thresholds(
        crowd_load,
        low_to_medium_threshold,
        medium_to_high_threshold,
    )

    base_risk = {
        "Normal": 0.20,
        "Warning": 0.60,
        "Critical": 0.95,
    }.get(prediction_label, 0.50)
    load_risk_add = {"Low": 0.0, "Medium": 0.08, "High": 0.15}[load_level]
    risk_score = max(0.0, min(1.0, base_risk + load_risk_add))

    if prediction_label == "Critical" or load_level == "High":
        occupancy_status = "UNSAFE"
        risk_alert = "Immediate response: restrict entry and inspect structure"
    elif prediction_label == "Warning" or load_level == "Medium":
        occupancy_status = "LIMITED"
        risk_alert = "Caution: control inflow and increase monitoring"
    else:
        occupancy_status = "SAFE"
        risk_alert = "No active alert"

    return {
        "load_level": load_level,
        "occupancy_status": occupancy_status,
        "risk_score": round(risk_score, 3),
        "risk_alert": risk_alert,
    }


def _safe_float(value: Any, default: float = 0.0) -> float:
    # ThingSpeak fields can occasionally be empty strings or malformed text.
    try:
        if value is None:
            return default
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return default
        return float(value)
    except (TypeError, ValueError):
        return default


def http_get_json(url: str, timeout: int = 15) -> Dict[str, Any]:
    request = Request(url, method="GET")
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def http_post_form(url: str, payload: Dict[str, Any], timeout: int = 15) -> str:
    data = urlencode(payload).encode("utf-8")
    request = Request(url, data=data, method="POST")
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def http_post_json(url: str, payload: Any, timeout: int = 15) -> str:
    data = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def push_powerbi_event(powerbi_push_url: str, row: Dict[str, Any]) -> str:
    # Power BI push/streaming endpoints accept an array of rows.
    payload = [row]
    return http_post_json(powerbi_push_url, payload)


def fetch_latest_feed(channel_id: str, read_api_key: str) -> Dict[str, Any]:
    url = (
        f"https://api.thingspeak.com/channels/{channel_id}/feeds/last.json"
        f"?api_key={read_api_key}"
    )
    return http_get_json(url)


def write_prediction(write_api_key: str, prediction_id: int, prediction_label: str) -> str:
    # Store class id in field4 and human-readable label in ThingSpeak status text.
    url = "https://api.thingspeak.com/update.json"
    payload = {
        "api_key": write_api_key,
        "field4": prediction_id,
        "status": f"stress={prediction_label}",
    }
    return http_post_form(url, payload)


def map_thingspeak_to_features(feed: Dict[str, Any]) -> Dict[str, float]:
    return {
        "crowd_load": _safe_float(feed.get("field1", 0.0), 0.0),
        "temperature": _safe_float(feed.get("field2", 0.0), 0.0),
        "pressure": _safe_float(feed.get("field3", 0.0), 0.0),
    }


def load_defaults_from_reference_csv(
    reference_csv: str, feature_columns: Iterable[str]
) -> Dict[str, float]:
    df = pd.read_csv(reference_csv)
    defaults: Dict[str, float] = {}
    for col in feature_columns:
        if col in df.columns:
            defaults[col] = float(pd.to_numeric(df[col], errors="coerce").mean())
    return defaults


def build_feature_row(
    feature_columns: Iterable[str],
    incoming_values: Dict[str, float],
    defaults: Dict[str, float],
) -> pd.DataFrame:
    row: Dict[str, float] = {}
    for col in feature_columns:
        if col in incoming_values:
            row[col] = float(incoming_values[col])
        else:
            row[col] = float(defaults.get(col, 0.0))
    return pd.DataFrame([row])


def infer_once(
    model_bundle: Dict[str, Any],
    incoming_values: Dict[str, float],
    reference_csv: str,
) -> Dict[str, Any]:
    model = model_bundle["model"]
    label_encoder = model_bundle["label_encoder"]
    feature_columns = model_bundle.get("feature_columns", ["crowd_load", "temperature", "pressure"])

    defaults = model_bundle.get("feature_defaults") or {}
    if len(defaults) == 0:
        defaults = load_defaults_from_reference_csv(reference_csv, feature_columns)

    X = build_feature_row(feature_columns, incoming_values, defaults)
    pred_id = int(model.predict(X)[0])
    pred_label = str(label_encoder.inverse_transform([pred_id])[0])

    return {
        "prediction_id": pred_id,
        "prediction_label": pred_label,
        "features_used": X.to_dict(orient="records")[0],
    }


def simulate_from_csv_rows(csv_path: str) -> Iterable[Dict[str, Any]]:
    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        yield {
            "field1": row.get("field1", 0.0),
            "field2": row.get("field2", 0.0),
            "field3": row.get("field3", 0.0),
            "created_at": row.get("created_at", "n/a"),
            "entry_id": row.get("entry_id", "n/a"),
        }


def main() -> None:
    load_env_file()

    parser = argparse.ArgumentParser(description="Live ThingSpeak inference with StressNet model")
    parser.add_argument("--model", default="stress_model.pkl", help="Path to model artifact")
    parser.add_argument(
        "--reference-data",
        default="synthetic_stress_data_3class.csv",
        help="Reference CSV used for fallback feature defaults",
    )
    parser.add_argument("--channel-id", default=os.getenv("THINGSPEAK_CHANNEL_ID"))
    parser.add_argument("--read-api-key", default=os.getenv("THINGSPEAK_READ_API_KEY"))
    parser.add_argument("--write-api-key", default=os.getenv("THINGSPEAK_WRITE_API_KEY"))
    parser.add_argument("--poll-interval", type=int, default=20, help="Seconds between polls")
    parser.add_argument(
        "--iterations",
        type=int,
        default=10,
        help="Number of loops to run (0 means run forever)",
    )
    parser.add_argument(
        "--push-prediction",
        action="store_true",
        help="Push prediction back to ThingSpeak field4/status",
    )
    parser.add_argument(
        "--simulate-csv",
        default="",
        help="Optional CSV for offline simulation (expects field1/field2/field3 columns)",
    )
    parser.add_argument(
        "--analytics-output",
        default="analytics_output/live_stress_events.csv",
        help="Append-only CSV for Power BI analytics ingestion",
    )
    parser.add_argument(
        "--status-output",
        default="analytics_output/current_status.csv",
        help="Single-row CSV snapshot for current occupancy/risk cards",
    )
    parser.add_argument(
        "--powerbi-push-url",
        default=os.getenv("POWERBI_PUSH_URL", ""),
        help="Optional Power BI push dataset endpoint for true live dashboard updates",
    )
    args = parser.parse_args()

    bundle = joblib.load(args.model)
    load_threshold_medium, load_threshold_high = estimate_load_thresholds(args.reference_data)

    print(
        "Load thresholds (from reference data): "
        f"low/medium={load_threshold_medium:.2f}, "
        f"medium/high={load_threshold_high:.2f}"
    )

    if args.simulate_csv:
        print(f"Running offline simulation from: {args.simulate_csv}")
        feeds = simulate_from_csv_rows(args.simulate_csv)
        for i, feed in enumerate(feeds, start=1):
            incoming = map_thingspeak_to_features(feed)
            result = infer_once(bundle, incoming, args.reference_data)
            status = derive_operational_status(
                result["prediction_label"],
                incoming["crowd_load"],
                load_threshold_medium,
                load_threshold_high,
            )
            row = {
                "event_time_utc": datetime.now(timezone.utc).isoformat(),
                "channel_id": "simulation",
                "source_created_at": feed.get("created_at", ""),
                "source_entry_id": feed.get("entry_id", ""),
                "crowd_load": incoming["crowd_load"],
                "temperature": incoming["temperature"],
                "pressure": incoming["pressure"],
                "prediction_id": result["prediction_id"],
                "prediction_label": result["prediction_label"],
                "load_level": status["load_level"],
                "occupancy_status": status["occupancy_status"],
                "risk_score": status["risk_score"],
                "risk_alert": status["risk_alert"],
                "write_back_enabled": False,
                "write_back_response": "",
            }
            append_analytics_row(args.analytics_output, row)
            write_status_snapshot(args.status_output, row)
            if args.powerbi_push_url:
                try:
                    push_response = push_powerbi_event(args.powerbi_push_url, row)
                    print(f"    Power BI push response: {push_response}")
                except Exception as exc:
                    print(f"    Power BI push failed: {exc}")
            print(
                f"[{i}] entry={feed.get('entry_id')} time={feed.get('created_at')} "
                f"prediction={result['prediction_label']} ({result['prediction_id']}) "
                f"load={status['load_level']} occupancy={status['occupancy_status']} "
                f"risk={status['risk_score']}"
            )
            print("    alert:", status["risk_alert"])
            print("    features:", result["features_used"])
        print(f"Saved analytics log to {args.analytics_output}")
        print(f"Saved latest status snapshot to {args.status_output}")
        return

    if not args.channel_id or not args.read_api_key:
        raise ValueError(
            "ThingSpeak channel id/read key missing. Set env vars or pass --channel-id and --read-api-key."
        )

    print("Starting live inference loop...")
    print(f"Channel: {args.channel_id}")
    if args.iterations == 0:
        print(f"Iterations: infinite, poll interval: {args.poll_interval}s")
    else:
        print(f"Iterations: {args.iterations}, poll interval: {args.poll_interval}s")

    i = 1
    while args.iterations == 0 or i <= args.iterations:
        feed = fetch_latest_feed(args.channel_id, args.read_api_key)
        incoming = map_thingspeak_to_features(feed)
        result = infer_once(bundle, incoming, args.reference_data)
        status = derive_operational_status(
            result["prediction_label"],
            incoming["crowd_load"],
            load_threshold_medium,
            load_threshold_high,
        )

        write_back_response = ""

        print(
            f"[{i}] entry={feed.get('entry_id')} time={feed.get('created_at')} "
            f"prediction={result['prediction_label']} ({result['prediction_id']}) "
            f"load={status['load_level']} occupancy={status['occupancy_status']} "
            f"risk={status['risk_score']}"
        )
        print("    alert:", status["risk_alert"])
        print("    features:", result["features_used"])

        if args.push_prediction:
            if not args.write_api_key:
                raise ValueError("Write API key required when --push-prediction is enabled")
            write_back_response = write_prediction(
                args.write_api_key,
                result["prediction_id"],
                result["prediction_label"],
            )
            print(f"    ThingSpeak write response: {write_back_response}")

        row = {
            "event_time_utc": datetime.now(timezone.utc).isoformat(),
            "channel_id": args.channel_id,
            "source_created_at": feed.get("created_at", ""),
            "source_entry_id": feed.get("entry_id", ""),
            "crowd_load": incoming["crowd_load"],
            "temperature": incoming["temperature"],
            "pressure": incoming["pressure"],
            "prediction_id": result["prediction_id"],
            "prediction_label": result["prediction_label"],
            "load_level": status["load_level"],
            "occupancy_status": status["occupancy_status"],
            "risk_score": status["risk_score"],
            "risk_alert": status["risk_alert"],
            "write_back_enabled": args.push_prediction,
            "write_back_response": write_back_response,
        }
        append_analytics_row(args.analytics_output, row)
        write_status_snapshot(args.status_output, row)
        if args.powerbi_push_url:
            try:
                push_response = push_powerbi_event(args.powerbi_push_url, row)
                print(f"    Power BI push response: {push_response}")
            except Exception as exc:
                print(f"    Power BI push failed: {exc}")

        if args.iterations == 0 or i < args.iterations:
            time.sleep(args.poll_interval)

        i += 1

    print(f"Saved analytics log to {args.analytics_output}")
    print(f"Saved latest status snapshot to {args.status_output}")


if __name__ == "__main__":
    main()
