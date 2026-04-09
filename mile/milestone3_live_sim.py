import time
import requests
import numpy as np
import pandas as pd
import joblib

# ===== THINGSPEAK CLOUD SETTINGS =====
# Write API Key matching your ESP32 firmware
WRITE_API_KEY = "23QZO8VUXRXAB3D9"

# Provide Channel ID & Read API Key to fetch actual incoming data
# (If omitted, the script will mathematically fallback to simulating the data locally)
READ_CHANNEL_ID = "3332291"  
READ_API_KEY = "1EY2D6WZE5OZDLBF"

MODEL_PATH = 'xgb_stress_classifier.pkl'

def simulate_edge_node_upload():
    """Simulates the ESP32 reading structural data and uploading it to ThingSpeak."""
    print("🌍 [EDGE NODE]: Reading physical sensors...")
    load = round(np.random.uniform(1000, 4800), 2)
    temp = round(np.random.uniform(5, 45), 2)
    pressure = round(np.random.uniform(93, 106), 2)
    
    print(f"   -> Sensor Data | Load: {load}kg | Temp: {temp}°C | Press: {pressure}kPa")
    
    # 1. Upload to ThingSpeak Cloud (Milestone 3 constraint)
    url = f"http://api.thingspeak.com/update?api_key={WRITE_API_KEY}&field1={temp}&field2={pressure}&field3={load}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print("   -> [CLOUD UPLOAD]: Success! Sent to ThingSpeak.")
        else:
            print(f"   -> [CLOUD UPLOAD]: Rate-limit / Failed ({response.status_code})")
    except Exception as e:
        print(f"   -> [CLOUD UPLOAD]: Error: {e}")
        
    return temp, pressure, load

def fetch_cloud_and_predict(model, fallback_data):
    """Simulates the Cloud Inference Engine pulling data from ThingSpeak & Predicting."""
    print("\n🧠 [ML ENGINE]: Fetching live cloud data & running inference...")
    temp, pressure, load = fallback_data
    
    # 2. Integrate live cloud data (Milestone 3 constraint)
    if READ_CHANNEL_ID != "YOUR_CHANNEL_ID":
        try:
            read_url = f"https://api.thingspeak.com/channels/{READ_CHANNEL_ID}/feeds.json?api_key={READ_API_KEY}&results=1"
            response = requests.get(read_url, timeout=5)
            if response.status_code == 200:
                feeds = response.json().get('feeds', [])
                if feeds:
                    item = feeds[0]
                    temp = float(item.get('field1', temp))
                    pressure = float(item.get('field2', pressure))
                    load = float(item.get('field3', load))
                    print("   -> [CLOUD FETCH]: Extracted live metrics from ThingSpeak database.")
        except Exception as e:
            print(f"   -> [CLOUD FETCH Error]: {e}")
    else:
        print("   -> [CLOUD FETCH]: No Channel ID set for READ access. Defaulting to local synchronized state pipeline.")

    # 3. Integrate with Trained ML Model
    # Formatting to match exactly what XGBoost expects: ['load_kg', 'temperature_c', 'pressure_kpa']
    input_df = pd.DataFrame([{
        'load_kg': load,
        'temperature_c': temp,
        'pressure_kpa': pressure
    }])
    
    prediction = model.predict(input_df)[0]
    status_map = {0: "🟢 NORMAL", 1: "🟡 WARNING", 2: "🔴 CRITICAL"}
    
    print(f"   => 📊 [STRESS PREDICTION]: {status_map.get(prediction, 'UNKNOWN')}")
    print("-" * 65)

def main():
    print("="*65)
    print("🚀 MILESTONE 3: LIVE CLOUD SIMULATION & ML PREDICTION ENGINE")
    print("="*65)
    
    try:
        model = joblib.load(MODEL_PATH)
        print("[System] XGBoost Model loaded successfully.")
    except Exception as e:
        print(f"[System] Failed to load model. Error: {e}")
        return

    print("\nStarting Continuous Feedback Loop...")
    try:
        # Loop replicates constant structural telemetry pinging
        # Limiting to 3 loops to avoid API rate limits during testing
        for i in range(3): 
            print(f"\n[ TIMESTEP: {i+1} ]")
            
            # Step 1: Push simulated sensory data to cloud
            latest_data = simulate_edge_node_upload()
            
            time.sleep(2) # Network delay mimic
            
            # Step 2: Ingest from cloud -> predict
            fetch_cloud_and_predict(model, latest_data)
            
            if i < 2:
                print("Waiting 15 seconds to respect ThingSpeak's rate limits...")
                time.sleep(15) 
            
    except KeyboardInterrupt:
        print("\nSimulation aborted.")

if __name__ == "__main__":
    main()
