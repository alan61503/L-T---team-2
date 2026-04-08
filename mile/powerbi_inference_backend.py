import time
import requests
import pandas as pd
import numpy as np
import joblib
import os

# ===== CONFIGURATION =====
# Place your ThingSpeak Read URL here when ready to pull real device data:
# Example: ""
THINGSPEAK_READ_URL = "https://api.thingspeak.com/channels/3332291/feeds.json?api_key=1EY2D6WZE5OZDLBF&results=1" 

MODEL_PATH = 'xgb_stress_classifier.pkl'
POWERBI_CSV_PATH = 'powerbi_live_feed.csv'

def main():
    print("="*60)
    print("⚙️ POWER BI REAL-TIME ML INFERENCE BACKEND")
    print("="*60)
    
    try:
        model = joblib.load(MODEL_PATH)
        print("[System] XGBoost Model loaded successfully.")
    except Exception as e:
        print(f"[Error] Failed to load model. Be sure Milestone 2 is complete: {e}")
        return

    print(f"[System] Analytics output streaming continuously into -> {POWERBI_CSV_PATH}")
    
    status_map = {0: "Normal", 1: "Warning", 2: "Critical"}
    
    # Initialize the structured CSV header for Power BI if it doesn't exist
    if not os.path.exists(POWERBI_CSV_PATH):
        pd.DataFrame(columns=['timestamp', 'temperature_c', 'pressure_kpa', 'load_kg', 'stress_status']).to_csv(POWERBI_CSV_PATH, index=False)

    print("\nRunning... (Press Ctrl+C to Stop)")
    
    while True:
        try:
            # 1. Fetch live IoT data (Fallback to simulated if ThingSpeak omitted)
            if THINGSPEAK_READ_URL != "":
                response = requests.get(THINGSPEAK_READ_URL, timeout=5)
                feeds = response.json().get('feeds', [])
                if feeds:
                    item = feeds[0]
                    timestamp = item.get('created_at')
                    temp = float(item.get('field1', 25))
                    pressure = float(item.get('field2', 100))
                    load = float(item.get('field3', 2000))
            else:
                timestamp = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                temp = round(float(np.random.uniform(5, 45)), 2)
                pressure = round(float(np.random.uniform(93, 106)), 2)
                load = round(float(np.random.uniform(1000, 4800)), 2)
            
            # 2. Run Data through XGBoost Model
            input_df = pd.DataFrame([{
                'load_kg': load,
                'temperature_c': temp,
                'pressure_kpa': pressure
            }])
            
            pred = model.predict(input_df)[0]
            status_text = status_map.get(pred, "Unknown")
            
            # 3. Log securely to CSV for Power BI DirectQuery reading
            new_row = pd.DataFrame([{
                'timestamp': timestamp,
                'temperature_c': temp,
                'pressure_kpa': pressure,
                'load_kg': load,
                'stress_status': status_text
            }])
            new_row.to_csv(POWERBI_CSV_PATH, mode='a', header=False, index=False)
            
            print(f"[{timestamp}] Power BI Updated -> Load: {load}kg | ML Logic Status: {status_text}")
            
            # Stream sync rate limit (15s matches ThingSpeak API)
            time.sleep(15)
            
        except KeyboardInterrupt:
            print("\nShutting down Power BI inference pipeline.")
            break
        except Exception as e:
            print(f"[Warning] Error in inference loop: {e}")
            time.sleep(15)

if __name__ == "__main__":
    main()
