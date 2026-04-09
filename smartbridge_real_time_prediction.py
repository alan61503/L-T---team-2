import requests
import json
import time
import pandas as pd
import joblib
import os
from datetime import datetime

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
CHANNEL_ID = '3332291'
READ_API_KEY = '1EY2D6WZE5OZDLBF'
THINGSPEAK_URL = f'https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds/last.json?api_key={READ_API_KEY}'

CSV_OUTPUT_PATH = 'smartbridge_live_predictions.csv'
MODEL_PATH = 'stress_xgboost_model.pkl'
ENCODER_PATH = 'label_encoder.pkl'
POLL_INTERVAL_SEC = 10

def initialize_csv():
    # If file doesn't exist, create it with headers
    if not os.path.exists(CSV_OUTPUT_PATH):
        df = pd.DataFrame(columns=['timestamp', 'load_kg', 'temperature', 'pressure', 'predicted_stress'])
        df.to_csv(CSV_OUTPUT_PATH, index=False)

def fetch_latest_data():
    try:
        response = requests.get(THINGSPEAK_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # Field mappings from ESP32:
        # field1: temperature
        # field2: pressure (convert Pa from BMP085 into hPa)
        # field3: load_kg
        temperature = float(data.get('field1') or 0.0)
        pressure = float(data.get('field2') or 0.0) / 100.0
        load_kg = float(data.get('field3') or 0.0)
        timestamp = data.get('created_at')
        
        return {
            'timestamp': timestamp,
            'load_kg': load_kg,
            'temperature': temperature,
            'pressure': pressure
        }
    except Exception as e:
        print(f"Error fetching data from ThingSpeak: {e}")
        return None

def main():
    print("Loading ML model and encoder...")
    if not os.path.exists(MODEL_PATH) or not os.path.exists(ENCODER_PATH):
        print(f"Error: {MODEL_PATH} or {ENCODER_PATH} not found. Please run training script first.")
        return

    model = joblib.load(MODEL_PATH)
    label_encoder = joblib.load(ENCODER_PATH)
    
    initialize_csv()
    
    print("Starting Real-Time Monitoring System...")
    print("Fetching live data from ThingSpeak...\n")
    
    last_timestamp = None
    
    while True:
        data = fetch_latest_data()
        
        if data and data['timestamp'] != last_timestamp:
            last_timestamp = data['timestamp']
            
            # Prepare input for ML model
            # Must match the order of features used during training: load_kg, temperature, pressure
            input_features = pd.DataFrame([{
                'load_kg': data['load_kg'],
                'temperature': data['temperature'],
                'pressure': data['pressure']
            }])
            
            # Predict
            pred_encoded = model.predict(input_features)[0]
            predicted_class = label_encoder.inverse_transform([pred_encoded])[0]
            
            # Current time for local logging
            local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"[{local_time}] Load: {data['load_kg']:.2f} kg | Temp: {data['temperature']:.2f} C | Pres: {data['pressure']:.2f} hPa")
            print(f"--> PREDICTED STRESS LEVEL: {predicted_class}")
            
            # Log to CSV
            prediction_record = {
                'timestamp': local_time,
                'load_kg': data['load_kg'],
                'temperature': data['temperature'],
                'pressure': data['pressure'],
                'predicted_stress': predicted_class
            }
            df_new = pd.DataFrame([prediction_record])
            df_new.to_csv(CSV_OUTPUT_PATH, mode='a', header=False, index=False)
            
        time.sleep(POLL_INTERVAL_SEC)

if __name__ == "__main__":
    main()
