import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os
from datetime import datetime, timedelta

# -------------------------------------------------------------------
# Generate Synthetic Data
# -------------------------------------------------------------------
def generate_synthetic_data(num_records=1000):
    np.random.seed(42)
    print(f"Generating {num_records} synthetic records...")

    base_time = datetime.now()
    timestamps = [(base_time - timedelta(seconds=i * 15)).strftime('%Y-%m-%d %H:%M:%S') for i in range(num_records)]

    load_kg = np.random.normal(loc=1.5, scale=2.5, size=num_records)
    load_kg = np.clip(load_kg, 0, 8)

    temperature_c = np.random.normal(loc=15, scale=15, size=num_records)
    temperature_c = np.clip(temperature_c, -20, 50)

    pressure_hpa = np.random.normal(loc=1000, scale=30, size=num_records)

    df = pd.DataFrame({
        'timestamp': timestamps,
        'load_kg': load_kg,
        'temperature': temperature_c,
        'pressure': pressure_hpa
    })

    return df

# -------------------------------------------------------------------
# UPDATED STRESS LOGIC (FIXED)
# -------------------------------------------------------------------
def assign_stress_level(row):
    load = row['load_kg']
    temp = row['temperature']
    pressure = row['pressure']

    # 🔴 PRIORITY 1: LOAD
    if load > 4:
        return 'Critical'

    # Environmental Safety
    env_safe = (0 <= temp <= 35) and (980 <= pressure <= 1020)

    # 🔴 PRIORITY 2: EXTREME CONDITIONS
    if temp > 40 or temp < -10:
        return 'Critical'

    if (2 <= load <= 4) and (temp > 36 or temp < 0) and (pressure < 970 or pressure > 1025):
        return 'Critical'

    # 🟡 WARNING
    if 2 <= load <= 4:
        return 'Warning'

    if 35 < temp <= 40 or -10 <= temp < 0:
        return 'Warning'

    if pressure < 970 or pressure > 1020:
        return 'Warning'

    # 🟢 NORMAL
    if load <= 2 and env_safe:
        return 'Normal'

    return 'Normal'

# -------------------------------------------------------------------
# VALIDATION FUNCTION (NEW 🔥)
# -------------------------------------------------------------------
def validate_stress_rules(row):
    load = row['load_kg']
    temp = row['temperature']
    pressure = row['pressure']
    label = row['stress_level']

    if load > 4:
        expected = 'Critical'
    elif temp > 40 or temp < -10:
        expected = 'Critical'
    elif (2 <= load <= 4) and (temp > 36 or temp < 0) and (pressure < 970 or pressure > 1025):
        expected = 'Critical'
    elif 2 <= load <= 4:
        expected = 'Warning'
    elif 35 < temp <= 40 or -10 <= temp < 0:
        expected = 'Warning'
    elif pressure < 970 or pressure > 1020:
        expected = 'Warning'
    else:
        expected = 'Normal'

    return label == expected

# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------
def main():
    df = generate_synthetic_data()

    print("Applying feature engineering rules...")
    df['stress_level'] = df.apply(assign_stress_level, axis=1)

    # 🔍 VALIDATION CHECK
    df['is_correct'] = df.apply(validate_stress_rules, axis=1)

    errors = df[df['is_correct'] == False]

    print("\nValidation Results:")
    print(f"Total Records: {len(df)}")
    print(f"Correct: {df['is_correct'].sum()}")
    print(f"Incorrect: {len(errors)}")

    if len(errors) > 0:
        print("\nSample Errors:")
        print(errors[['load_kg', 'temperature', 'pressure', 'stress_level']].head())

    # Save dataset
    df.to_csv('smartbridge_historical_data.csv', index=False)

    print("\nDataset Summary:")
    print(df['stress_level'].value_counts())

    # ML Training
    X = df[['load_kg', 'temperature', 'pressure']]
    y = df['stress_level']

    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

    print("\nTraining XGBoost Model...")
    model = xgb.XGBClassifier(
        objective='multi:softprob',
        num_class=3,
        eval_metric='mlogloss',
        seed=42
    )

    model.fit(X_train, y_train)

    # Evaluation
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\nModel Accuracy: {accuracy * 100:.2f}%")

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

    # Save model
    joblib.dump(model, 'stress_xgboost_model.pkl')
    joblib.dump(label_encoder, 'label_encoder.pkl')

    print("\nModel and encoder saved successfully!")

# -------------------------------------------------------------------
if __name__ == "__main__":
    main()
