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
3. Milestone 3 - Live Data Simulation and Model Integration: In Progress
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
	- Random Forest
	- Decision Tree
	- Logistic Regression
- automatic best-model selection,
- model serialisation to `stress_model.pkl`.

### 3. Latest Validated Performance

On `synthetic_stress_data_3class.csv` (held-out test split):

- Random Forest Accuracy: 0.85
- Decision Tree Accuracy: 0.805
- Logistic Regression Accuracy: 0.88
- Selected best model: Logistic Regression

## Repository Contents

- `data_generation.py`: synthetic data generation script
- `prepare_3class_dataset.py`: 3-class label preparation script
- `train_stress_model.py`: model training, evaluation, and export
- `synthetic_stress_data.csv`: base synthetic dataset
- `synthetic_stress_data_3class.csv`: prepared three-class dataset
- `stress_model.pkl`: saved best model artifact
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

The repository now includes working dataset-generation and machine-learning components for Milestone 2. The model has been validated for single-record and batch inference and is ready for integration into the live data pipeline in Milestone 3.