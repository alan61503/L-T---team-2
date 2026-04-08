import argparse
import json
import os
import time
from typing import Any, Dict, Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd


def _safe_float(value: Any, default: float = 0.0) -> float:
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


def load_env_file(path: str = ".env") -> None:
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, value)


def http_post_form(url: str, payload: Dict[str, Any], timeout: int = 15) -> str:
    data = urlencode(payload).encode("utf-8")
    request = Request(url, data=data, method="POST")
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def upload_sensor_row(
    write_api_key: str,
    crowd_load: float,
    temperature: float,
    pressure: float,
    status_text: str = "simulated",
) -> str:
    url = "https://api.thingspeak.com/update.json"
    payload = {
        "api_key": write_api_key,
        "field1": crowd_load,
        "field2": temperature,
        "field3": pressure,
        "status": status_text,
    }
    return http_post_form(url, payload)


def row_stream_from_csv(csv_path: str) -> Iterable[Dict[str, Any]]:
    df = pd.read_csv(csv_path)
    for _, row in df.iterrows():
        # Accept both ThingSpeak-style and synthetic dataset schemas.
        crowd_load = row.get("field1", row.get("crowd_load", row.get("force", 0.0)))
        temperature = row.get("field2", row.get("temperature", 0.0))
        pressure = row.get("field3", row.get("pressure", 0.0))

        yield {
            "crowd_load": _safe_float(crowd_load, 0.0),
            "temperature": _safe_float(temperature, 0.0),
            "pressure": _safe_float(pressure, 0.0),
            "source_time": row.get("created_at", row.get("timestamp", "n/a")),
            "source_entry": row.get("entry_id", "n/a"),
        }


def main() -> None:
    load_env_file()

    parser = argparse.ArgumentParser(
        description="Simulate real-time sensor data and upload to ThingSpeak cloud"
    )
    parser.add_argument(
        "--source-csv",
        default="thingspeak_demo.csv",
        help="CSV with sensor data (supports field1/field2/field3 or crowd_load/temperature/pressure)",
    )
    parser.add_argument(
        "--write-api-key",
        default=os.getenv("THINGSPEAK_WRITE_API_KEY"),
        help="ThingSpeak write API key (defaults to THINGSPEAK_WRITE_API_KEY env var)",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=10,
        help="Seconds between sensor uploads",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=0,
        help="How many uploads to run (0 means loop forever over CSV rows)",
    )
    parser.add_argument(
        "--status-prefix",
        default="sim",
        help="Prefix text written to ThingSpeak status field",
    )
    args = parser.parse_args()

    if not args.write_api_key:
        raise ValueError("ThingSpeak write API key missing. Set --write-api-key or THINGSPEAK_WRITE_API_KEY.")

    rows = list(row_stream_from_csv(args.source_csv))
    if len(rows) == 0:
        raise ValueError(f"No rows found in source CSV: {args.source_csv}")

    print("Starting cloud sensor simulation...")
    print(f"Source CSV: {args.source_csv}")
    print(f"Rows available: {len(rows)}")
    if args.iterations == 0:
        print(f"Iterations: infinite, poll interval: {args.poll_interval}s")
    else:
        print(f"Iterations: {args.iterations}, poll interval: {args.poll_interval}s")

    index = 0
    sent = 0
    while args.iterations == 0 or sent < args.iterations:
        row = rows[index % len(rows)]
        status_text = (
            f"{args.status_prefix} src_entry={row['source_entry']} src_time={row['source_time']}"
        )
        response = upload_sensor_row(
            args.write_api_key,
            row["crowd_load"],
            row["temperature"],
            row["pressure"],
            status_text,
        )

        sent += 1
        print(
            f"[{sent}] crowd_load={row['crowd_load']:.2f} temp={row['temperature']:.2f} "
            f"pressure={row['pressure']:.2f} -> ThingSpeak response={response}"
        )

        index += 1
        if args.iterations == 0 or sent < args.iterations:
            time.sleep(args.poll_interval)


if __name__ == "__main__":
    main()
