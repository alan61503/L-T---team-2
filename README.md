# StressNet: Structural Stress Prediction

StressNet is an IoT + AI concept project for monitoring structural stress in tourist bridges, skywalks, and viewing platforms. It combines live sensor streams, cloud processing, machine learning inference, and dashboard visualization to classify safety risk levels in near real time.

## Project Goal

Build a monitoring workflow that can:

- collect force, temperature, and pressure data from sensors,
- process and store data in the cloud,
- predict stress state using an ML model,
- present live status and alerts for safety operators.

## Problem Statement

Traditional structural monitoring often relies on manual checks and fixed load assumptions. That approach can miss sudden overload or changing environmental conditions. StressNet targets proactive safety by continuously estimating structural stress and highlighting risk trends.

## System Architecture

The current architecture (see `flowchat.jpeg`) follows this pipeline:

1. Sensor Layer: force, temperature, pressure sensors
2. Edge Layer: ESP32 microcontroller collects and forwards readings
3. Ingestion Layer: WiFi/MQTT upload to ThingSpeak cloud
4. Cloud Processing: Azure services and data processing components
5. AI/ML Layer: stress prediction model outputs risk class
6. Visualization Layer: backend API and Power BI dashboard
7. Alerting Layer: visual indicators and email/SMS notifications

## Stress Classification

Planned prediction classes:

- Safe (low stress)
- Warning (moderate stress)
- Danger/Critical (high stress)

## Hardware Components

Mentioned hardware stack:

- ESP32-S3 microcontroller
- DHT22 temperature sensor
- BMP180 pressure sensor
- HX711 load cell amplifier
- 5 kg load cell (force sensor)
- LED status indicator

## Software and Cloud Stack

- Circuit simulation/design: Cirkit Designer
- Sensor ingestion: ThingSpeak
- Cloud services and processing: Microsoft Azure
- Model training notebooks/workflows: Google Colab
- Dashboard and analytics: Microsoft Power BI

## Planned Milestones

1. Architecture design and end-to-end data flow definition
2. Dataset generation and ML model training/validation
3. Live data simulation and model integration
4. Output storage and dashboard visualization
5. Result analysis and industry interpretation

## Repository Contents

This repository currently contains documentation and architecture artifacts:

- `Structural_Stress_Prediction.docx`: project brief and milestone-level deliverables
- `StressNet1.docx`: detailed concept document with components, flow, and expected outcomes
- `flowchat.jpeg`: visual architecture flow diagram
- `README.md`: this summary

## Current Status

At the moment, the repository appears to be in a documentation/planning phase. Source code for firmware, backend services, data pipeline, and ML model training/deployment is not yet present in this branch.

## Suggested Next Build Steps

1. Add firmware code for ESP32 sensor acquisition and cloud publishing.
2. Add a cloud function/service for preprocessing and inference.
3. Add ML training scripts/notebooks and versioned model artifacts.
4. Add dashboard dataset/schema definitions and alert rules.
5. Add deployment/configuration docs for reproducible setup.