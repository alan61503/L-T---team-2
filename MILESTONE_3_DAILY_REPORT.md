# Milestone 3 Daily Report

**Date:** 07 April 2026  
**Project:** StressNet - Structural Stress Prediction

## 1. Objective

To simulate real-time structural sensor data flow and integrate the trained machine learning model with live cloud data in order to generate continuous stress predictions.

## 2. Work Completed Today

### 2.1 Integration of Live IoT Data Pipeline

- Existing ESP32 and ThingSpeak data format has been aligned with the inference pipeline.
- Live field mapping is confirmed as:
  - Field 1 -> Force / Crowd Load
  - Field 2 -> Temperature
  - Field 3 -> Pressure

### 2.2 Real-Time Data Retrieval from Cloud

- Implemented ThingSpeak latest-feed retrieval via REST API in `live_thingspeak_inference.py`.
- Polling interval support was added to match ThingSpeak update behaviour.
- Retrieved payload is validated and mapped before inference.

### 2.3 Data Preprocessing for Inference

- Standardised live input schema to model schema.
- Mapped fields as:
  - crowd_load <- field1
  - temperature <- field2
  - pressure <- field3
- Added fallback defaults for optional model features (`vibration`, `elevation`) to ensure inference stability.

### 2.4 ML Model Integration

- Integrated saved model artifact `stress_model.pkl` in the live inference workflow.
- Added per-record prediction execution for incoming data points.

### 2.5 Real-Time Stress Classification

- Predictions are output as human-readable labels:
  - Normal (Safe)
  - Warning (Moderate Stress)
  - Critical (High Risk)
- Continuous prediction mode implemented for repeated polling.

### 2.6 Cloud Feedback Loop Implementation

- Added optional write-back to ThingSpeak:
  - prediction id pushed to `field4`
  - prediction label pushed to ThingSpeak `status`
- This enables centralised monitoring of raw signals and inferred stress state.

### 2.7 Live Simulation Validation

- Implemented offline simulation mode using `thingspeak_data.csv` to validate streaming logic.
- Pipeline supports varying inputs and produces corresponding class predictions.

## 3. Key Technical Outputs

- Live data ingestion pipeline (ThingSpeak -> local inference system)
- Integrated ML inference system using `stress_model.pkl`
- Real-time prediction generation workflow (`live_thingspeak_inference.py`)
- Cloud feedback mechanism for predicted stress levels

## 4. Validation Results

- Real-time inference pipeline executes successfully with valid predictions.
- Prediction generation is stable with no missing outputs in test runs.
- Model outputs update dynamically as inputs change.

## 5. Assessment Against Milestone 3

Milestone 3 criteria have been met:

- Simulation of real-time sensor data: Completed
- Integration of live cloud data with ML model: Completed
- Real-time stress prediction generation: Completed

## 6. Updated System Flow

Sensors (Force, Temp, Pressure)  
-> ESP32 Microcontroller  
-> WiFi Transmission  
-> ThingSpeak Cloud  
-> Data Retrieval (API)  
-> ML Model (`stress_model.pkl`)  
-> Stress Prediction  
-> ThingSpeak / Dashboard Storage

## 7. Configuration and Security Notes

ThingSpeak credentials must be provided through environment variables (do not hardcode in source files):

- `THINGSPEAK_CHANNEL_ID`
- `THINGSPEAK_READ_API_KEY`
- `THINGSPEAK_WRITE_API_KEY`

Use `.env.example` as the template and keep actual secrets in a local `.env` file.
