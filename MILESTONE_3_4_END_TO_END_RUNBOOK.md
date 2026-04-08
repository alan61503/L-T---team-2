# Milestone 3 + 4 End-to-End Runbook

This runbook executes both targets as a complete live pipeline.

## Target Coverage

### Milestone 3: Live Data Simulation & Model Integration

- Simulate real-time sensor data for `load`, `temperature`, and `pressure` and upload to cloud (ThingSpeak).
- Integrate live cloud data with trained ML model for real-time stress predictions.

### Milestone 4: Analytics Output & Dashboard Visualization

- Store real-time sensor + prediction outputs in structured files.
- Display occupancy status, load levels, and risk alerts on a live dashboard.

## Prerequisites

1. ThingSpeak channel with fields:
   - `field1`: crowd_load
   - `field2`: temperature
   - `field3`: pressure
   - `field4`: prediction_id (optional write-back)
2. `.env` file with:

```env
THINGSPEAK_CHANNEL_ID=YOUR_CHANNEL_ID
THINGSPEAK_READ_API_KEY=YOUR_READ_API_KEY
THINGSPEAK_WRITE_API_KEY=YOUR_WRITE_API_KEY
```

3. Trained model artifact exists: `stress_model.pkl`

## Option A (Recommended): Full Local Live Demo in 3 Terminals

### Terminal 1: Simulate sensor stream to cloud (Milestone 3 part 1)

```powershell
python simulate_sensor_to_thingspeak.py --source-csv thingspeak_demo.csv --poll-interval 10 --iterations 0
```

This continuously uploads simulated sensor rows to ThingSpeak.

### Terminal 2: Cloud inference + structured output (Milestone 3 part 2 + Milestone 4 part 1)

```powershell
python live_thingspeak_inference.py --channel-id $env:THINGSPEAK_CHANNEL_ID --read-api-key $env:THINGSPEAK_READ_API_KEY --write-api-key $env:THINGSPEAK_WRITE_API_KEY --push-prediction --poll-interval 10 --iterations 0
```

This continuously:

- pulls latest cloud sensor record,
- runs ML prediction,
- optionally writes prediction back to ThingSpeak,
- writes structured analytics output:
  - `analytics_output/live_stress_events.csv`
  - `analytics_output/current_status.csv`

### Terminal 3: Live dashboard (Milestone 4 part 2)

```powershell
pip install -r requirements_dashboard.txt
streamlit run live_dashboard_streamlit.py
```

Open the displayed local URL (usually `http://localhost:8501`).

## Option B: Cloud-Hosted Real-Time Dashboard

Deploy `cloud_live_dashboard.py` via `render.yaml`.

- Default mode uses simulation CSV in cloud.
- Set `USE_SIMULATION=false` + ThingSpeak env vars for true cloud sensor source.

## Validation Checklist

- [ ] Terminal 1 prints successful ThingSpeak update responses.
- [ ] Terminal 2 prints live predictions and risk levels continuously.
- [ ] `analytics_output/live_stress_events.csv` keeps growing.
- [ ] `analytics_output/current_status.csv` updates latest row.
- [ ] Dashboard cards and trend charts update automatically.

## Common Issues

1. No new inference rows:
   - Verify ThingSpeak read key/channel id.
   - Confirm simulator is writing using correct write key.
2. Dashboard not updating:
   - Keep inference process running.
   - Check Streamlit auto-refresh interval.
3. Permission errors:
   - Ensure scripts run from repository root.
