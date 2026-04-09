import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import joblib
import time
import os
from datetime import datetime, timedelta

def generate_synthetic_data(num_records=1000):
    np.random.seed(42)
    print(f"Generating {num_records} synthetic records...")
    
    # Generate readable local timestamps without UTC tracking
    base_time = datetime.now()
    timestamps = [(base_time - timedelta(seconds=i * 15)).strftime('%Y-%m-%d %H:%M:%S') for i in range(num_records)]
    
    # Generate sensor data
    # Realistic desktop prototype parameters
    # Normal load: 0 - 2 kg
    # Warning load: 2 - 4 kg
    # Critical load: > 4 kg
    load_kg = np.random.normal(loc=1.5, scale=2.5, size=num_records)
    load_kg = np.clip(load_kg, 0, 8) # prevent negative load, cap at 8 kg
    
    temperature_c = np.random.normal(loc=25, scale=8, size=num_records)
    temperature_c = np.clip(temperature_c, 5, 50)
    
    # Generate pressure in hPa as requested in rules
    pressure_hpa = np.random.normal(loc=1000, scale=30, size=num_records)
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'load_kg': load_kg,
        'temperature': temperature_c,
        'pressure': pressure_hpa
    })
    
    return df

def assign_stress_level(row):
    load = row['load_kg']
    temp = row['temperature']
    pressure = row['pressure']
    
    # Evaluate Environmental Safety (strict definition)
    env_safe = (temp < 35) and (980 <= pressure <= 1020)
    
    # Priority 1: CRITICAL
    if load > 4 and not env_safe:
        return 'Critical'
    if (2 <= load <= 4) and (temp > 36) and (pressure < 970 or pressure > 1025):
        return 'Critical'
        
    # Priority 2: WARNING
    # Edge case downgrade
    if load > 4 and env_safe:
        return 'Warning'
    if 2 <= load <= 4:
        return 'Warning'
    if temp > 35:
        return 'Warning'
    if pressure < 970 or pressure > 1020:
        return 'Warning'
        
    # Priority 3: NORMAL
    if load <= 2 and temp < 35 and (980 <= pressure <= 1020):
        return 'Normal'
        
    # Fallback default for any undefined transition zones (like pressure 970-980)
    return 'Normal'

def main():
    # 1. Generate Data
    df = generate_synthetic_data()
    
    # 2. Feature Engineering
    print("Applying feature engineering rules...")
    df['stress_level'] = df.apply(assign_stress_level, axis=1)
    
    # Save the synthetic dataset
    dataset_path = 'smartbridge_historical_data.csv'
    df.to_csv(dataset_path, index=False)
    print(f"Dataset generated and saved to {dataset_path}")
    print("\nDataset Summary:")
    print(df['stress_level'].value_counts())
    
    # 3. Model Training Preparation
    X = df[['load_kg', 'temperature', 'pressure']]
    y = df['stress_level']
    
    # Encode target labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    # Train-Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)
    
    # 4. Train XGBoost Model
    print("\nTraining XGBoost Classifier...")
    model = xgb.XGBClassifier(
        objective='multi:softprob',
        num_class=3,
        eval_metric='mlogloss',
        seed=42
    )
    
    model.fit(X_train, y_train)
    
    # 5. Evaluate Model
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nModel Accuracy: {accuracy * 100:.2f}%")
    
    target_names = label_encoder.inverse_transform([0, 1, 2])
    # The order of classes depends on the unique values encountered, which might not be 0->Critical, 1->Normal, 2->Warning. 
    # Let's get the distinct classes from the encoder.
    classes_found = label_encoder.classes_
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=classes_found))
    
    # 6. Save Model and Encoder
    model_path = 'stress_xgboost_model.pkl'
    encoder_path = 'label_encoder.pkl'
    
    joblib.dump(model, model_path)
    joblib.dump(label_encoder, encoder_path)
    print(f"Model saved to {model_path}")
    print(f"Label Encoder saved to {encoder_path}")

if __name__ == "__main__":
    main()
