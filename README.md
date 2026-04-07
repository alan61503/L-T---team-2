# StressNet: Structural Stress Prediction

StressNet is an IoT + AI project for monitoring structural stress in tourist bridges, skywalks, and viewing platforms. The system combines sensor data, cloud ingestion, machine learning inference, and dashboard visualisation to classify risk levels in near real time.

## Project Objective

Develop an end-to-end workflow that can:

- collect force/load, temperature, and pressure data,
- preprocess and store observations,
- classify structural stress as Normal, Warning, or Critical,
- support safety monitoring and alerting.

## System Architecture

The architecture diagram in `flowchat.jpeg` follows this pipeline:

1. Sensor Layer: force/load, temperature, pressure sensors
2. Edge Layer: ESP32 microcontroller collection and forwarding
3. Ingestion Layer: WiFi/MQTT to ThingSpeak
4. Cloud Processing Layer: Azure-based processing components
5. AI/ML Layer: stress classification inference
6. Visualisation Layer: backend API and Power BI dashboard
7. Alerting Layer: visual and message-based notifications

## Milestone Status

1. Milestone 1 - Architecture Design: Completed
2. Milestone 2 - Dataset Generation and ML Model Development: Completed
3. Milestone 3 - Live Data Simulation and Model Integration: Completed
4. Milestone 4 - Output Storage and Dashboard Visualisation: Pending
5. Milestone 5 - Results and Interpretation: Pending

## Milestone 2 Completion Evidence

### 1. Synthetic Dataset Generation and Preprocessing

- Synthetic historical dataset generated: `synthetic_stress_data.csv`
- Three-class labelled dataset prepared: `synthetic_stress_data_3class.csv`
- Label classes used: `Normal`, `Warning`, `Critical`

### 2. ML Model Training and Validation

Implemented training and evaluation workflow in `train_stress_model.py` with:

- train/test split,
- label encoding,
- multi-model comparison:
	- Decision Tree
	- Logistic Regression
- automatic best-model selection,
- model serialisation to `stress_model.pkl`.

### 3. Latest Validated Performance

On `synthetic_stress_data_3class.csv` (held-out test split):

- Decision Tree Accuracy: 0.805
- Logistic Regression Accuracy: 0.88
- Selected best model: Logistic Regression

## Repository Contents

- `data_generation.py`: synthetic data generation script
- `prepare_3class_dataset.py`: 3-class label preparation script
- `train_stress_model.py`: model training, evaluation, and export
- `live_thingspeak_inference.py`: live ThingSpeak polling, model inference, and optional write-back
- `synthetic_stress_data.csv`: base synthetic dataset
- `synthetic_stress_data_3class.csv`: prepared three-class dataset
- `thingspeak_data.csv`: sample streamed ThingSpeak records for simulation/testing
- `stress_model.pkl`: saved best model artifact
- `MILESTONE_3_DAILY_REPORT.md`: formal Milestone 3 daily completion report
- `flowchat.jpeg`: architecture flow diagram
- `Structural_Stress_Prediction.docx`: milestone-level project brief
- `StressNet1.docx`: detailed concept document

## How to Reproduce Milestone 2

Run from the project root:

```powershell
python prepare_3class_dataset.py
python train_stress_model.py --data synthetic_stress_data_3class.csv
```

Expected outcome:

- model performance metrics printed to terminal,
- best model exported as `stress_model.pkl`.

## Current Status

The repository now includes completed Milestone 2 and Milestone 3 components. The system supports live cloud data retrieval from ThingSpeak, real-time stress inference using `stress_model.pkl`, and optional prediction feedback to ThingSpeak.

## Milestone 3 Completion Evidence

### 1. Live Data Integration

- ThingSpeak field mapping implemented:
	- `field1 -> crowd_load`
	- `field2 -> temperature`
	- `field3 -> pressure`
- Cloud retrieval from latest ThingSpeak feed is implemented in `live_thingspeak_inference.py`.

### 2. Model Integration and Real-Time Inference

- `stress_model.pkl` is loaded directly in the live pipeline.
- Real-time prediction labels are generated continuously: `Normal`, `Warning`, `Critical`.
- Missing optional features are handled with fallback defaults to preserve inference stability.

### 3. Cloud Feedback Loop

- Optional prediction write-back support implemented:
	- prediction id -> `field4`
	- prediction label -> ThingSpeak `status`

### 4. Security Configuration

Credentials are handled through environment variables and not hardcoded:

- `THINGSPEAK_CHANNEL_ID`
- `THINGSPEAK_READ_API_KEY`
- `THINGSPEAK_WRITE_API_KEY`

Use `.env.example` as the setup template.

### 5. Run Instructions for Milestone 3

Offline simulation mode:

```powershell
python live_thingspeak_inference.py --simulate-csv thingspeak_data.csv
```

Live ThingSpeak polling mode:

```powershell
python live_thingspeak_inference.py --channel-id <CHANNEL_ID> --read-api-key <READ_KEY> --iterations 10 --poll-interval 20
```

Live polling with prediction feedback to ThingSpeak:

```powershell
python live_thingspeak_inference.py --channel-id <CHANNEL_ID> --read-api-key <READ_KEY> --write-api-key <WRITE_KEY> --push-prediction --iterations 10 --poll-interval 20
```