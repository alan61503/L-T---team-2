import pandas as pd
import numpy as np

np.random.seed(42)

n_samples = 1000

time = pd.date_range(start="2025-01-01", periods=n_samples, freq="h")

# Simulate multiple locations (e.g., tourist bridges)
locations = [
    {"name": "Bridge_A", "lat": 13.0827, "lon": 80.2707, "elev": 6},   # Chennai
    {"name": "Bridge_B", "lat": 12.9716, "lon": 77.5946, "elev": 920}, # Bangalore
    {"name": "Bridge_C", "lat": 11.0168, "lon": 76.9558, "elev": 411}, # Coimbatore
]

# Randomly assign locations
loc_choices = np.random.choice(len(locations), n_samples)

latitude = [locations[i]["lat"] + np.random.normal(0, 0.001) for i in loc_choices]
longitude = [locations[i]["lon"] + np.random.normal(0, 0.001) for i in loc_choices]
elevation = np.array([locations[i]["elev"] + np.random.normal(0, 5) for i in loc_choices])
location_name = [locations[i]["name"] for i in loc_choices]

# Sensor data
crowd_load = np.random.randint(0, 500, n_samples)
temperature = np.random.uniform(15, 45, n_samples)

# Pressure slightly depends on elevation (higher → lower pressure)
pressure = 1013 - (elevation * 0.12) + np.random.normal(0, 5, n_samples)

vibration = np.random.uniform(0, 5, n_samples)

# Stress formula
stress = (
    0.5 * crowd_load +
    0.3 * temperature +
    0.2 * pressure +
    10 * vibration +
    0.1 * elevation +
    np.random.normal(0, 20, n_samples)
)
status = []

for s, vib in zip(stress, vibration):
    if s < 350 and vib < 2:
        status.append("Normal")
    elif s < 650:
        status.append("Warning")
    else:
        status.append("Critical")

# DataFrame
df = pd.DataFrame({
    "timestamp": time,
    "location": location_name,
    "latitude": latitude,
    "longitude": longitude,
    "elevation": elevation,
    "crowd_load": crowd_load,
    "temperature": temperature,
    "pressure": pressure,
    "vibration": vibration,
    "stress": stress,
    "status": status
})

# Save file
df.to_csv("synthetic_stress_data.csv", index=False)

# Download (for Colab)
from google.colab import files
files.download("synthetic_stress_data.csv")
