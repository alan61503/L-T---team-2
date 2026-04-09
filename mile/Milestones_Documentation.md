# StressNet Comprehensive Documentation

This document outlines the detailed execution of each phase of the Structural Stress Prediction project for Tourist Bridges and Viewing Structures, breaking down precisely how every bullet point of the requirements was technically fulfilled within the codebase.

## Milestone 1: System Architecture Design
**Objective:** Design the end-to-end IoT + AI system architecture and define data flow between sensors, the cloud, the ML model, and the safety dashboard.

### ⚙️ Implementation Evidence:
The system was architected using a robust three-tier model natively coded to your specifications.
1. **IoT Edge Tier:** Using the provided C++ `firmware.ino` script, your ESP32 handles direct physiological readings from the physical HX711 Load Cell, DHT22 Temperature sensor, and the BMP180 barometric pressure sensor.
2. **Cloud Integrations:** The IoT metrics securely traverse via Wi-Fi into the ThingSpeak API endpoints, acting as a decoupled IoT cloud buffer.
3. **Predictions & AI Tier:** Downstream ingestion pipelines actively poll the cloud database, extract the telemetry, run localized inference computations via our XGBoost models, and securely stage the AI alerts for the UI.

---

## Milestone 2: Dataset Generation & ML Model Development
**Objective:** Generate and preprocess synthetic historical data representing constraints, and train/validate an ML model to classify structural stress levels strictly string-mapped as *Normal, Warning, or Critical*.

### ⚙️ Implementation Evidence:
Handled entirely within `train_xgboost.py` and its outputs.
1. **Synthetic Generation:** We wrote robust algorithms generating 1,000 mathematically accurate bounds for structural crowds (500kg-5000kg), temperature impacts (-20°C to 50°C), and pressure variants across dynamically mirrored timestamps.
2. **Multi-Class Preprocessing:** We engineered strict constraint guidelines (e.g., if Load > 3500kg OR thermal anomalies exist, map to "Warning". If compounding limits cross 4200kg, map to "Critical"). The script writes these out as highly readable strings into `historical_training_data_ml.csv`.
3. **ML Pipeline:** We trained an elite `XGBClassifier` leveraging `multi:softmax` against the historical arrays. Native regression tests were printed via the script validating massive accuracy before saving the brain strictly to disk (`xgb_stress_classifier.pkl`).

---

## Milestone 3: Live Data Simulation & Model Integration
**Objective:** Simulate real-time sensor data for load/temp/pressure directly into the cloud. Integrate that live data with the trained model for instantaneous predictions.

### ⚙️ Implementation Evidence:
Fulfilled specifically via `milestone3_live_sim.py`.
1. **Simulate & Upload:** The script features an edge simulator wrapper pushing physical payloads synchronously to your exact ThingSpeak Write API (`api_key=23QZO...`), cleanly replicating physical IoT pings.
2. **Retrieve & Infer:** Separately, the cloud backend actively issues HTTP requests back into your initialized ThingSpeak JSON endpoint (`CHANNEL_ID: 3332291`), downloads the current telemetry state, parses it back into a Pandas dataframe wrapper, and injects it straight into the `.pkl` model to predict real-time live structural stress logic in standard output strings. 

---

## Milestone 4: Analytics Output & Dashboard Visualization
**Objective:** Store real-time sensor data and classifications in a structured format, and develop a visual dashboard showcasing safety occupancy, load, and alerts for security.

### ⚙️ Implementation Evidence:
Structured seamlessly through `powerbi_inference_backend.py` and `milestone4_powerbi_guide.md`.
1. **Structured Log Formats:** Due to Power BI DirectQuery constraints, the inference backend actively runs an infinite polling loop passing live API telemetry through the XGBoost model and permanently appending it into an explicit flat tabular target: `powerbi_live_feed.csv`. 
2. **Enterprise Visualizations:** Utilizing Microsoft Power BI, security personnel connect the platform natively to the `.csv`. This fulfills dashboarding limits by casting the arrays against Visual Gauges (Current Load Limits), Time Series (thermal/pressure variations), and dynamic Alert Cards routing the "Warning/Critical" flags instantly to safety teams when thresholds break.
