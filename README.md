# StressNet: Structural Stress Prediction for Tourist Bridges

This project is an end-to-end real-time IoT and Artificial Intelligence system designed to monitor and predict the structural stress levels of tourist bridges.

## Components

1. **IoT Edge Device:** ESP32 with HX711 Load Cell, DHT22 (Temperature), and BMP180 (Pressure).
2. **Cloud Service:** ThingSpeak for logging and fetching telemetry data.
3. **Machine Learning Base:** XGBoost classifier trained on a synthetic dataset representing rigorous structural physics (accounting for thermal expansion and freezing threats). 
4. **Real-time Engine:** A Python backend fetching remote IoT telemetry, applying the ML inference, and continuously logging outcomes.
5. **Dashboard Presentation (Historical):** Microsoft Power BI for localized forensic review.
6. **Live Mobile Dashboard (Real-Time):** Blynk IoT App for instant sensor visualization and automated Push/Email safety alerts.

## Pipeline Walkthrough

### 1. IoT Hardware Setup (`smartbridge_esp32.ino`)
Upload the Arduino script to your ESP32. It continuously samples from the HX711, DHT22, and BMP180, acting as the edge node.
1. Replace `YOUR_WIFI_SSID` and `YOUR_WIFI_PASSWORD` with network credentials.
2. Replace `YOUR_THINGSPEAK_WRITE_API_KEY` with the ThingSpeak Channel's Write API key.
3. Configure ThingSpeak Fields:
   - `field1`: `temperature`
   - `field2`: `pressure`
   - `field3`: `load_kg`

### 2. Dataset Generation and ML Training (`smartbridge_data_generation_training.py`)
To emulate realistic bridge usage before deploying, we synthesize over 1000+ records and apply rigorous thresholds for our model to learn. This logic explicitly safeguards against thermal expansion (>40°C) and winter freezing (<-10°C) threats.
1. Install dependencies: `pip install -r requirements.txt`
2. Run the script: `python smartbridge_data_generation_training.py`
3. This will create:
   - `smartbridge_historical_data.csv`: Historical dataset
   - `stress_xgboost_model.pkl`: Exported XGBoost model
   - `label_encoder.pkl`: Exported Label Encoder

### 3. Real-Time Inference Platform (`smartbridge_real_time_prediction.py`)
This script ties the real-world IoT readings to the trained ML model. It periodically polls ThingSpeak for the latest load, temperature, and pressure. It runs this payload through XGBoost, generates live predictions, and automatically streams the final result to Blynk.
1. Update `YOUR_THINGSPEAK_CHANNEL_ID` and `YOUR_THINGSPEAK_READ_API_KEY`.
2. Update `BLYNK_AUTH_TOKEN` with your Blynk Device Token.
3. Run the platform: `python smartbridge_real_time_prediction.py`
4. The platform creates `smartbridge_live_predictions.csv` locally, and blasts all synchronized data directly to the Blynk Cloud.

### 4. Blynk Mobile Dashboard Integration (Live Alerting)
The Python script operates as an invisible bridge between ThingSpeak and Blynk, allowing you to monitor the strict AI prediction directly on your phone.

**Setting Up the Datastreams:**
1. Log into `blynk.cloud` and create a Template ("StressNet").
2. Create 4 Virtual Datastreams:
   * **V1 (Temperature):** Double (Min 0, Max 100)
   * **V2 (Pressure):** Double (Min 600, Max 1100)
   * **V3 (Load):** Double (Min 0, Max 10)
   * **V4 (Stress Status):** String (No min/max required)
3. Set up two **Events** in your Template to trigger when the Python script outputs severe threat codes:
   * Event Code `warning_alert` (Warning type) -> Enable Push/Email
   * Event Code `critical_alert` (Critical type) -> Enable Push/Email

**Mobile Phone Setup:**
1. Open the Blynk IoT App and add your device.
2. Add three **Gauge** widgets mapped to V1, V2, and V3.
3. Add a **Labeled Value** widget mapped to V4.
*As long as your Python backend is running, the dashboard updates instantly, and your phone will receive lock-screen push notifications the second the AI registers a Critical event!*

### 5. Power BI Historical Dashboard Integration
To complete the situational awareness suite, Power BI allows stakeholders to visualize the risks in forensic detail.

**Setting Up the Live Data Source:**
1. **Direct from Local CSV Prediction Output:**
   * Go to Power BI > "Get Data" > "Text/CSV"
   * Point to `smartbridge_live_predictions.csv`.

**Creating Visuals:**
Configure exactly as below:
1. **Line chart (Load vs Time):** X-axis: `timestamp`, Y-axis: `load_kg`
2. **Line chart (Temperature and Pressure Trends):** X-axis: `timestamp`, Y-axis 1: `temperature`, Y-axis 2: `pressure`
3. **Card (Current Stress Level):** Most recent `predicted_stress`. 
4. **Table:** Include `timestamp`, `load_kg`, `temperature`, `pressure`, `predicted_stress`. Sort by descending timestamp.

**Conditional Formatting Options (Visual Polish):**
On your Table or Stress Level card backgrounds (Format Visual > Background > Conditional Formatting > rules):
* If `predicted_stress` is "Normal" -> #00B050 (Green)
* If `predicted_stress` is "Warning" -> #FFC000 (Yellow)
* If `predicted_stress` is "Critical" -> #FF0000 (Red)

## Executive Insights & Real-World Impact
This structural health monitoring apparatus brings "invisible" structural fatigue into obvious view:
* **Crowd Safety:** Continuous active monitoring prevents catastrophic structural failure caused by flash crowds or tourist events exceeding standard pedestrian density parameters.
* **Rapid Alerting System:** Through the integration of the Blynk REST API, site managers receive instant lock-screen notifications the exact second the Python ML engine calculates a critical failure limit.
* **Invisible Threat Mitigation:** Correlating extreme weather data with raw gravity loads alerts operators to severe freeze-fracturing or thermal expansion weaknesses. Proactive decision-making shifts maintenance from a "reactive repair" stance to an exact science.
