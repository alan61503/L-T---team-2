# StressNet: Structural Stress Prediction for Tourist Bridges

This project is an end-to-end real-time IoT and Artificial Intelligence system designed to monitor and predict the structural stress levels of tourist bridges.

## Components

1. **IoT Edge Device:** ESP32 with HX711 Load Cell, DHT11 (Temperature), and BMP280 (Pressure).
2. **Cloud Service:** ThingSpeak for logging and fetching telemetry data.
3. **Machine Learning Base:** XGBoost classifier trained on a synthetic dataset representing bridge physics. 
4. **Real-time Engine:** A Python backend fetching remote IoT telemetry, applying the ML inference, and continuously logging outcomes.
5. **Dashboard Presentation:** Microsoft Power BI.

## Pipeline Walkthrough

### 1. IoT Hardware Setup (`smartbridge_esp32.ino`)
Upload the Arduino script to your ESP32. It continuously samples from the HX711, DHT11, and BMP280, acting as the edge node.
1. Replace `YOUR_WIFI_SSID` and `YOUR_WIFI_PASSWORD` with network credentials.
2. Replace `YOUR_THINGSPEAK_WRITE_API_KEY` with the ThingSpeak Channel's Write API key.
3. Configure ThingSpeak Fields:
   - `field1`: `load_kg`
   - `field2`: `temperature`
   - `field3`: `pressure`

### 2. Dataset Generation and ML Training (`smartbridge_data_generation_training.py`)
To emulate realistic bridge usage before deploying, we synthesize over 1500+ records and apply rigorous thresholds for our model to learn.
1. Install dependencies: `pip install -r requirements.txt`
2. Run the script: `python smartbridge_data_generation_training.py`
3. This will create:
   - `smartbridge_historical_data.csv`: Historical dataset
   - `stress_xgboost_model.pkl`: Exported XGBoost model
   - `label_encoder.pkl`: Exported Label Encoder

### 3. Real-Time Inference Platform (`smartbridge_real_time_prediction.py`)
This script ties the real-world IoT readings to the trained ML model. It periodically polls ThingSpeak for the latest load and temperature, runs it through XGBoost, and generates live predictions.
1. Update `YOUR_THINGSPEAK_CHANNEL_ID` and `YOUR_THINGSPEAK_READ_API_KEY`.
2. Run the platform: `python smartbridge_real_time_prediction.py`
3. The platform creates `smartbridge_live_predictions.csv` and streams the live classifications to standard output.

### 4. Power BI Real-Time Dashboard Integration

To complete the situational awareness suite, Power BI allows stakeholders to visualize the risks in near real-time.

**Setting Up the Live Data Source:**
There are two ways to connect in Power BI:
1. **Direct from Local CSV Prediction Output (Recommended for complete view):**
   * Go to Power BI > "Get Data" > "Text/CSV"
   * Point to `smartbridge_live_predictions.csv`.
2. **Direct from ThingSpeak (Raw Data):**
   * Go to "Get Data" > "Web"
   * Enter the URL: `https://api.thingspeak.com/channels/YOUR_CHANNEL_ID/feeds.csv?api_key=YOUR_READ_API_KEY`

**Creating Visuals:**
Configure exactly as below:
1. **Line chart (Load vs Time):** X-axis: `timestamp`, Y-axis: `load_kg` (or Field 1)
2. **Line chart (Temperature and Pressure Trends):** X-axis: `timestamp`, Y-axis 1: `temperature`, Y-axis 2: `pressure`
3. **Card (Current Load):** Most recent `load_kg` 
4. **Card (Current Stress Level):** Most recent `predicted_stress`. Text dynamically changes based on predictions.
5. **Gauge (Load vs Safe Capacity):** Value: `load_kg`, Target: 400 (Critical line), Max: 600
6. **Table:** Include `timestamp`, `load_kg`, `temperature`, `pressure`, `predicted_stress`. Sort by descending timestamp.

**Conditional Formatting Options (Visual Polish):**
On your Table or Stress Level card backgrounds (Format Visual > Background > Conditional Formatting > rules):
* If `predicted_stress` is "Normal" -> #00B050 (Green)
* If `predicted_stress` is "Warning" -> #FFC000 (Yellow)
* If `predicted_stress` is "Critical" -> #FF0000 (Red)

**Dashboard Automation:**
1. Enable `Page Refresh` in Power BI desktop format pane (e.g. set to refresh every 10 seconds).
2. Alternatively, configure a Personal Gateway in Power BI Services for continuous web updates.

## Executive Insights & Real-World Impact
This structural health monitoring apparatus brings "invisible" structural fatigue into obvious view:
* **Crowd Safety:** Continuous active monitoring prevents catastrophic structural failure caused by flash crowds or tourist events exceeding standard pedestrian density parameters.
* **Overload Detection:** The immediate transition from "Warning" to "Critical" provides local authorities vital minutes to restrict bridge access prior to physical yielding mechanisms occurring.
* **Early Warning System (EWS):** Correlating temperature data with raw gravity loads alerts operators to thermal expansion weaknesses exacerbating weight conditions. Proactive decision-making shifts maintenance from a "reactive repair" stance to an exact science.
