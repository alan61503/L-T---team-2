# Milestone 4: Analytics Output and Power BI Dashboard

This guide uses the project pipeline to generate structured analytics output and visualize it in Power BI for security personnel.

It supports two dashboard modes:

- Near-real-time: CSV ingestion (`analytics_output/*.csv`)
- True live: direct push to Power BI push/streaming endpoint

## 1) Structured Analytics Output

The updated `live_thingspeak_inference.py` now produces two CSV outputs:

- `analytics_output/live_stress_events.csv`: append-only event log for trend/time analysis
- `analytics_output/current_status.csv`: single latest row for current status cards

### Output columns

- `event_time_utc`
- `channel_id`
- `source_created_at`
- `source_entry_id`
- `crowd_load`
- `temperature`
- `pressure`
- `prediction_id`
- `prediction_label`
- `load_level` (`Low`, `Medium`, `High`)
- `occupancy_status` (`SAFE`, `LIMITED`, `UNSAFE`)
- `risk_score` (0.0 to 1.0)
- `risk_alert`
- `write_back_enabled`
- `write_back_response`

## 2) Generate Data for Dashboard

Run offline simulation to create data quickly:

```powershell
python live_thingspeak_inference.py --simulate-csv thingspeak_demo.csv --model stress_model.pkl --reference-data synthetic_stress_data_3class.csv
```

For live polling mode:

```powershell
python live_thingspeak_inference.py --channel-id <CHANNEL_ID> --read-api-key <READ_KEY> --iterations 50 --poll-interval 20
```

For true live Power BI push mode:

```powershell
python live_thingspeak_inference.py --channel-id <CHANNEL_ID> --read-api-key <READ_KEY> --iterations 500 --poll-interval 10 --powerbi-push-url <POWERBI_PUSH_URL>
```

You can also store the push URL in `.env` using `POWERBI_PUSH_URL`.

## 3) Power BI Live Setup (Recommended for Real-Time)

1. In Power BI Service, create a push/streaming dataset with API ingestion.
2. Add fields matching the analytics output columns listed above.
3. Copy the generated push URL.
4. Set it as `POWERBI_PUSH_URL` in your environment or pass `--powerbi-push-url`.
5. Run live inference so each new event is pushed immediately.
6. Build dashboard visuals directly on this live dataset.

This gives near-instant updates without waiting for scheduled refresh.

## 4) Connect Power BI to Output Files (Fallback / Historical Analysis)

1. Open Power BI Desktop.
2. Select `Get Data` -> `Text/CSV`.
3. Load `analytics_output/live_stress_events.csv`.
4. Load `analytics_output/current_status.csv`.
5. In Power Query, set data types:
   - `event_time_utc`, `source_created_at` -> Date/Time
   - `crowd_load`, `temperature`, `pressure`, `risk_score` -> Decimal Number
   - `prediction_id`, `source_entry_id` -> Whole Number

## 5) Recommended Dashboard Layout (Security View)

Use these visuals on one page:

- Card: Current occupancy status from `current_status[occupancy_status]`
- Card: Current load level from `current_status[load_level]`
- Card: Current risk score from `current_status[risk_score]`
- Card/Text: Current risk alert from `current_status[risk_alert]`
- Line chart: `risk_score` over `event_time_utc`
- Line chart: `crowd_load` over `event_time_utc`
- Stacked column chart: count of `prediction_label` by hour
- Table: latest 20 events with timestamp, load, prediction, occupancy, alert

## 6) Useful DAX Measures

Create these measures in Power BI:

```DAX
Events Count = COUNTROWS(live_stress_events)

Critical Events =
CALCULATE(
    COUNTROWS(live_stress_events),
    live_stress_events[prediction_label] = "Critical"
)

Warning Events =
CALCULATE(
    COUNTROWS(live_stress_events),
    live_stress_events[prediction_label] = "Warning"
)

Unsafe Events =
CALCULATE(
    COUNTROWS(live_stress_events),
    live_stress_events[occupancy_status] = "UNSAFE"
)

Average Risk Score = AVERAGE(live_stress_events[risk_score])
```

## 7) Auto Refresh Recommendations

For near-real-time CSV dashboards:

- Keep the Python inference script running.
- In Power BI Desktop, use `Refresh` periodically during demo.
- For Power BI Service publishing, configure a gateway and scheduled refresh.

For true live dashboards:

- Use Power BI push/streaming dataset mode (Section 3).
- Keep the inference process running continuously.
- Updates appear as new events are posted.

## 8) Milestone 4 Completion Checklist

- [x] Real-time inference output stored in structured format
- [x] Occupancy status included (`SAFE`, `LIMITED`, `UNSAFE`)
- [x] Current load level included (`Low`, `Medium`, `High`)
- [x] Risk alerts included in each event
- [x] Dashboard-ready files generated for Power BI
- [x] Optional true live Power BI push integration available
