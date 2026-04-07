import argparse

import numpy as np
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic structural stress data")
    parser.add_argument("--samples", type=int, default=1000, help="Number of rows to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--output",
        default="synthetic_stress_data.csv",
        help="Output CSV path",
    )
    args = parser.parse_args()

    if args.samples <= 0:
        raise ValueError("--samples must be a positive integer")

    rng = np.random.default_rng(args.seed)
    n_samples = args.samples

    timestamps = pd.date_range(start="2025-01-01", periods=n_samples, freq="h")

    # Simulate multiple locations (e.g., tourist bridges)
    locations = [
        {"name": "Bridge_A", "lat": 13.0827, "lon": 80.2707, "elev": 6},
        {"name": "Bridge_B", "lat": 12.9716, "lon": 77.5946, "elev": 920},
        {"name": "Bridge_C", "lat": 11.0168, "lon": 76.9558, "elev": 411},
    ]

    loc_names = np.array([loc["name"] for loc in locations], dtype=object)
    loc_lats = np.array([loc["lat"] for loc in locations], dtype=float)
    loc_lons = np.array([loc["lon"] for loc in locations], dtype=float)
    loc_elevs = np.array([loc["elev"] for loc in locations], dtype=float)

    loc_choices = rng.integers(0, len(locations), size=n_samples)

    latitude = loc_lats[loc_choices] + rng.normal(0, 0.001, n_samples)
    longitude = loc_lons[loc_choices] + rng.normal(0, 0.001, n_samples)
    elevation = loc_elevs[loc_choices] + rng.normal(0, 5, n_samples)
    location_name = loc_names[loc_choices]

    crowd_load = rng.integers(0, 500, n_samples)
    temperature = rng.uniform(15, 45, n_samples)
    vibration = rng.uniform(0, 5, n_samples)

    # Pressure slightly depends on elevation (higher altitude -> lower pressure)
    pressure = 1013 - (elevation * 0.12) + rng.normal(0, 5, n_samples)

    stress = (
        0.5 * crowd_load
        + 0.3 * temperature
        + 0.2 * pressure
        + 10 * vibration
        + 0.1 * elevation
        + rng.normal(0, 20, n_samples)
    )

    # Vectorized class labeling is faster and simpler than row-wise loops.
    status = np.where((stress < 350) & (vibration < 2), "Normal", np.where(stress < 650, "Warning", "Critical"))

    df = pd.DataFrame(
        {
            "timestamp": timestamps,
            "location": location_name,
            "latitude": latitude,
            "longitude": longitude,
            "elevation": elevation,
            "crowd_load": crowd_load,
            "temperature": temperature,
            "pressure": pressure,
            "vibration": vibration,
            "stress": stress,
            "status": status,
        }
    )

    df.to_csv(args.output, index=False)
    print(f"Saved {len(df)} rows to {args.output}")


if __name__ == "__main__":
    main()
