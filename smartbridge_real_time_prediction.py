import requests
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

# Blynk Configuration
BLYNK_AUTH_TOKEN = 'tNFRlKZG_fppspfLJNcaiE7HB4OzMjjB'
BLYNK_BASE_URL = "https://blynk.cloud/external/api"

CSV_OUTPUT_PATH = 'smartbridge_live_predictions.csv'
MODEL_PATH = 'stress_xgboost_model.pkl'
ENCODER_PATH = 'label_encoder.pkl'
POLL_INTERVAL_SEC = 10

# Cooldown (avoid spam alerts)
LAST_ALERT_TIME = {
    "CRITICAL": 0,
    "WARNING": 0
}
ALERT_COOLDOWN = 60  # seconds

# -------------------------------------------------------------------

def initialize_csv():
    if not os.path.exists(CSV_OUTPUT_PATH):
        df = pd.DataFrame(columns=['timestamp', 'load_kg', 'temperature', 'pressure', 'predicted_stress'])
        df.to_csv(CSV_OUTPUT_PATH, index=False)

# -------------------------------------------------------------------

def fetch_latest_data():
    try:
        response = requests.get(THINGSPEAK_URL, timeout=5)
        response.raise_for_status()
        data = response.json()

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

# -------------------------------------------------------------------

def push_all_to_blynk(temp, pressure, load, prediction_text):
    try:
        url = f"{BLYNK_BASE_URL}/batch/update?token={BLYNK_AUTH_TOKEN}&V1={temp}&V2={pressure}&V3={load}&V4={prediction_text}"
        response = requests.get(url, timeout=3)

        if response.status_code == 200:
            print("✅ Data pushed to Blynk (V1-V4)")

    except Exception as e:
        print(f"❌ Failed to push to Blynk: {e}")

# -------------------------------------------------------------------

def trigger_blynk_event(predicted_class):
    global LAST_ALERT_TIME

    current_time = time.time()
    predicted_class = predicted_class.upper()

    try:
        # 🔴 CRITICAL ALERT
        if predicted_class == "CRITICAL":
            if current_time - LAST_ALERT_TIME["CRITICAL"] > ALERT_COOLDOWN:
                url = f"{BLYNK_BASE_URL}/logEvent?token={BLYNK_AUTH_TOKEN}&code=critical_alert&description=🚨 Critical Stress Detected!"
                requests.get(url, timeout=3)
                LAST_ALERT_TIME["CRITICAL"] = current_time
                print("🚨 Critical Alert Sent!")

        # 🟡 WARNING ALERT
        elif predicted_class == "WARNING":
            if current_time - LAST_ALERT_TIME["WARNING"] > ALERT_COOLDOWN:
                url = f"{BLYNK_BASE_URL}/logEvent?token={BLYNK_AUTH_TOKEN}&code=warning_alert&description=⚠️ Warning Stress Level!"
                requests.get(url, timeout=3)
                LAST_ALERT_TIME["WARNING"] = current_time
                print("⚠️ Warning Alert Sent!")

    except Exception as e:
        print(f"❌ Failed to trigger event: {e}")

# -------------------------------------------------------------------

def main():
    print("🔄 Loading ML model and encoder...")

    if not os.path.exists(MODEL_PATH) or not os.path.exists(ENCODER_PATH):
        print("❌ Model or encoder not found!")
        return

    model = joblib.load(MODEL_PATH)
    label_encoder = joblib.load(ENCODER_PATH)

    initialize_csv()

    print("🚀 Real-Time Monitoring Started...\n")

    last_timestamp = None

    while True:
        data = fetch_latest_data()

        if data and data['timestamp'] != last_timestamp:
            last_timestamp = data['timestamp']

            input_features = pd.DataFrame([{
                'load_kg': data['load_kg'],
                'temperature': data['temperature'],
                'pressure': data['pressure']
            }])

            # Prediction
            pred_encoded = model.predict(input_features)[0]
            predicted_class = label_encoder.inverse_transform([pred_encoded])[0]

            local_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            print(f"[{local_time}] Load: {data['load_kg']:.2f} kg | Temp: {data['temperature']:.2f}°C | Pressure: {data['pressure']:.2f} hPa")
            print(f"👉 Predicted Stress: {predicted_class}")

            # Push to Blynk
            push_all_to_blynk(
                data['temperature'],
                data['pressure'],
                data['load_kg'],
                predicted_class
            )

            # Trigger Alerts
            trigger_blynk_event(predicted_class)

            # Save to CSV
            df_new = pd.DataFrame([{
                'timestamp': local_time,
                'load_kg': data['load_kg'],
                'temperature': data['temperature'],
                'pressure': data['pressure'],
                'predicted_stress': predicted_class
            }])

            df_new.to_csv(CSV_OUTPUT_PATH, mode='a', header=False, index=False)

        time.sleep(POLL_INTERVAL_SEC)

# -------------------------------------------------------------------

if __name__ == "__main__":
    main()
