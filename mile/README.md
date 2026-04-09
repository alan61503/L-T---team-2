# Structural Stress Prediction for Tourist Bridges & Viewing Structures (StressNet)

This repository contains an end-to-end intelligence framework for real-time structural health monitoring. By integrating edge IoT sensors with a high-performance XGBoost Machine Learning classifier, the system continuously monitors crowd load, temperature variability, and pressure conditions to dynamically classify safe occupancy limits (Normal, Warning, or Critical) for tourists platforms.

## 🚀 Key Features
- **IoT Edge Processing:** Full ESP32 firmware parsing physical kinematic variables via DHT22, BMP180, and HX711 sensors.
- **ThingSpeak Cloud Integration:** Bi-directional data pipeline uploading metrics and streaming analytics via the ThingSpeak REST API limit constraints.
- **Machine Learning Inference:** A robust XGBoost Multi-Class classifier trained on physics and structural stress thresholds.
- **Real-Time Analytics:** A continuous background Python engine writing live telemetry logs explicitly formatted for seamless integration with Microsoft Power BI.

## 📂 Project Structure
- `firmware.ino` - ESP32 C++ code for handling edge sensor logic and cloud syncing.
- `architecture.md` - Complete technical flow architecture (Milestone 1).
- `train_xgboost.py` - Pre-processes local limits, combines ThingSpeak data, and outputs the trained machine learning model natively (Milestone 2).
- `milestone3_live_sim.py` - Modular simulation testing bridging physical payload formats to the AWS/ThingSpeak cloud ecosystem (Milestone 3).
- `powerbi_inference_backend.py` - The core production loop. Pulls exact physical data from ThingSpeak, runs the AI logic, and pushes continuous risk updates to `powerbi_live_feed.csv`.
- `milestone4_powerbi_guide.md` - Explicit visual design documentation for securely connecting the pipeline output into Microsoft Power BI (Milestone 4).
- `analysis.md` - Concluding analytical interpretations mapping structural risks (Milestone 5).

## ⚙️ Installation & Usage (Native Environment)
1. Ensure a standard Python 3.8+ root installation is running on your machine.
2. Install the system dependencies directly to your global environment via pip:
   ```bash
   pip install pandas numpy xgboost scikit-learn requests
   ```
3. If leveraging hardware, flash `firmware.ino` to your ESP32, ensuring `DHTPIN 18`, `HX711_DT 4`, `SCL 2`, and `SDA 1` are physically wired as mapped.
4. Run the data inference platform to begin Power BI syncing:
   ```bash
   python powerbi_inference_backend.py
   ```
*(Note: To integrate real hardware readings, plug your unique ThingSpeak IDs into the `THINGSPEAK_READ_URL` endpoints natively available inside the root python files).*
