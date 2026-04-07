import argparse
import json
import os
import time
from typing import Any, Dict, Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import joblib
import pandas as pd


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
    parser.add_argument("--iterations", type=int, default=10, help="Number of loops to run")
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
    args = parser.parse_args()

    bundle = joblib.load(args.model)

    if args.simulate_csv:
        print(f"Running offline simulation from: {args.simulate_csv}")
        feeds = simulate_from_csv_rows(args.simulate_csv)
        for i, feed in enumerate(feeds, start=1):
            incoming = map_thingspeak_to_features(feed)
            result = infer_once(bundle, incoming, args.reference_data)
            print(
                f"[{i}] entry={feed.get('entry_id')} time={feed.get('created_at')} "
                f"prediction={result['prediction_label']} ({result['prediction_id']})"
            )
            print("    features:", result["features_used"])
        return

    if not args.channel_id or not args.read_api_key:
        raise ValueError(
            "ThingSpeak channel id/read key missing. Set env vars or pass --channel-id and --read-api-key."
        )

    print("Starting live inference loop...")
    print(f"Channel: {args.channel_id}")
    print(f"Iterations: {args.iterations}, poll interval: {args.poll_interval}s")

    for i in range(1, args.iterations + 1):
        feed = fetch_latest_feed(args.channel_id, args.read_api_key)
        incoming = map_thingspeak_to_features(feed)
        result = infer_once(bundle, incoming, args.reference_data)

        print(
            f"[{i}] entry={feed.get('entry_id')} time={feed.get('created_at')} "
            f"prediction={result['prediction_label']} ({result['prediction_id']})"
        )
        print("    features:", result["features_used"])

        if args.push_prediction:
            if not args.write_api_key:
                raise ValueError("Write API key required when --push-prediction is enabled")
            response = write_prediction(
                args.write_api_key,
                result["prediction_id"],
                result["prediction_label"],
            )
            print(f"    ThingSpeak write response: {response}")

        if i < args.iterations:
            time.sleep(args.poll_interval)


if __name__ == "__main__":
    main()
