import pandas as pd
import numpy as np
import requests
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib

# ====== CONFIGURATION ======
# Provide your ThingSpeak Channel ID and Read API Key here to fetch actual historical data
THINGSPEAK_CHANNEL_ID = "3332291" 
THINGSPEAK_READ_API_KEY = "1EY2D6WZE5OZDLBF"
NUM_SYNTHETIC_SAMPLES = 1000
# ===========================

def fetch_thingspeak_data(channel_id, read_api_key, results=500):
    """
    Fetches real historical sensor data from ThingSpeak via API.
    Based on firmware: field1=Temp, field2=Pressure, field3=Load
    """
    url = f"https://api.thingspeak.com/channels/{channel_id}/feeds.json?api_key={read_api_key}&results={results}"
    print(f"Attempting to fetch data from ThingSpeak...")
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            feeds = data.get('feeds', [])
            if not feeds:
                return pd.DataFrame()
                
            records = []
            for item in feeds:
                try:
                    records.append({
                        'timestamp': item.get('created_at', pd.Timestamp.now().isoformat()),
                        'temperature_c': float(item.get('field1', 0)),
                        'pressure_kpa': float(item.get('field2', 0)),
                        'load_kg': float(item.get('field3', 0))
                    })
                except (ValueError, TypeError):
                    continue
                    
            df = pd.DataFrame(records)
            print(f"Successfully fetched {len(df)} records from ThingSpeak.")
            return df
        else:
            print(f"Failed to fetch data from ThingSpeak. Status code: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        print(f"ThingSpeak fetch bypassed/failed: {e}")
        return pd.DataFrame()

def generate_synthetic_data(num_samples):
    """
    Generates synthetic historical data for structural modeling constraints.
    """
    print(f"Generating {num_samples} synthetic sensor samples...")
    # Load constraints
    load_kg = np.random.uniform(500, 5000, num_samples)
    # Environmental constraints
    temperature_c = np.random.uniform(-20, 50, num_samples)
    pressure_kpa = np.random.uniform(90, 110, num_samples)
    
    end_time = pd.Timestamp.now()
    timestamps = [end_time - pd.Timedelta(seconds=15*i) for i in range(num_samples)]
    timestamps.reverse()
    
    return pd.DataFrame({
        'timestamp': [ts.isoformat() for ts in timestamps],
        'temperature_c': temperature_c,
        'pressure_kpa': pressure_kpa,
        'load_kg': load_kg
    })

def determine_stress(row):
    """
    Preprocess logic establishing ground truths for AI training based on physics.
    0: Normal, 1: Warning, 2: Critical
    """
    load = row['load_kg']
    temp = row['temperature_c']
    pressure = row['pressure_kpa']
    
    critical_load = load > 4200
    critical_temp = temp > 40 or temp < -10
    critical_pressure = pressure > 105 or pressure < 95
    
    if critical_load and (critical_temp or critical_pressure):
        return 2 # Critical
    elif critical_load:
        return 2 # Critical
    elif load > 3500 or critical_temp or critical_pressure:
        return 1 # Warning
    else:
        return 0 # Normal

def main():
    # 1. Take Data From ThingSpeak
    ts_data = fetch_thingspeak_data(THINGSPEAK_CHANNEL_ID, THINGSPEAK_READ_API_KEY)
    
    # 2. Generate Synthetic Historical Data
    synth_data = generate_synthetic_data(NUM_SYNTHETIC_SAMPLES)
    
    # 3. Combine Sets
    if not ts_data.empty:
        # Reorder df columns
        if 'timestamp' in ts_data.columns:
            ts_data = ts_data[['timestamp', 'temperature_c', 'pressure_kpa', 'load_kg']]
        else:
            ts_data = ts_data[['temperature_c', 'pressure_kpa', 'load_kg']]
        combined_data = pd.concat([ts_data, synth_data], ignore_index=True)
    else:
        print("Note: Using primarily synthetic data (ThingSpeak API details omitted, yielding base load).")
        combined_data = synth_data
        
    # Preprocessing labels
    print("Filtering and labeling data structure constraints...")
    combined_data['stress_level'] = combined_data.apply(determine_stress, axis=1)
    
    # Save the CSV mapped to strings for the user
    output_csv = combined_data.copy()
    status_map = {0: 'Normal', 1: 'Warning', 2: 'Critical'}
    output_csv['stress_level'] = output_csv['stress_level'].map(status_map)
    output_csv.to_csv('historical_training_data_ml.csv', index=False)
    
    # 4. Train the ML Model (Uses the 0,1,2 numerics natively)
    X = combined_data[['load_kg', 'temperature_c', 'pressure_kpa']]
    y = combined_data['stress_level']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("\nTraining XGBoost Classifier (Using Gradient Boosting instead of RF)...")
    model = XGBClassifier(
        objective='multi:softmax', 
        num_class=3, 
        eval_metric='mlogloss',
        random_state=42, 
        n_estimators=100, 
        max_depth=6
    )
    model.fit(X_train, y_train)
    
    print("\nEvaluating Model on Validation Set...")
    y_pred = model.predict(X_test)
    
    print(f"Model Accuracy: {accuracy_score(y_test, y_pred)*100:.2f}%")
    print("Classification Metrics Overview:")
    print(classification_report(y_test, y_pred, target_names=['Normal', 'Warning', 'Critical']))
    
    # Save Model to disk
    joblib.dump(model, 'xgb_stress_classifier.pkl')
    print("XGBoost model saved to -> xgb_stress_classifier.pkl!")

if __name__ == "__main__":
    main()
