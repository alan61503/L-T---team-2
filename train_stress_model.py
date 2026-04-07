import pandas as pd
import argparse

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.pipeline import Pipeline
import joblib


def _resolve_columns(df: pd.DataFrame) -> tuple[str, str, str, str]:
    # Support both the requested schema and the existing repository schema.
    force_col = "force" if "force" in df.columns else "crowd_load"
    temp_col = "temperature"
    pressure_col = "pressure"
    label_col = "label" if "label" in df.columns else "status"

    required = [force_col, temp_col, pressure_col, label_col]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    return force_col, temp_col, pressure_col, label_col


def _normalize_labels(series: pd.Series) -> pd.Series:
    # Normalize common naming variants so class mapping is consistent.
    synonyms = {
        "safe": "Normal",
        "normal": "Normal",
        "warning": "Warning",
        "danger": "Critical",
        "critical": "Critical",
    }
    return series.astype(str).str.strip().str.lower().map(synonyms).fillna(series)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train structural stress classifiers")
    parser.add_argument(
        "--data",
        default="synthetic_stress_data.csv",
        help="Path to CSV dataset",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.data)
    print("Dataset preview:")
    print(df.head())

    force_col, temp_col, pressure_col, label_col = _resolve_columns(df)

    df[label_col] = _normalize_labels(df[label_col])

    le = LabelEncoder()
    df["label_encoded"] = le.fit_transform(df[label_col])

    print("\nLabel mapping:")
    for cls_name, cls_id in zip(le.classes_, le.transform(le.classes_)):
        print(f"{cls_name} -> {cls_id}")

    feature_cols = [force_col, temp_col, pressure_col]
    for optional_col in ["vibration", "elevation"]:
        if optional_col in df.columns:
            feature_cols.append(optional_col)

    print("\nUsing features:", feature_cols)
    X = df[feature_cols]
    y = df["label_encoded"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    rf = RandomForestClassifier(
        n_estimators=600,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)

    dt = DecisionTreeClassifier(class_weight="balanced", random_state=42)
    dt.fit(X_train, y_train)
    y_pred_dt = dt.predict(X_test)

    lr = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(max_iter=3000, random_state=42)),
        ]
    )
    lr.fit(X_train, y_train)
    y_pred_lr = lr.predict(X_test)

    acc_rf = accuracy_score(y_test, y_pred_rf)
    acc_dt = accuracy_score(y_test, y_pred_dt)
    acc_lr = accuracy_score(y_test, y_pred_lr)

    candidates = {
        "Random Forest": (rf, y_pred_rf, acc_rf),
        "Decision Tree": (dt, y_pred_dt, acc_dt),
        "Logistic Regression": (lr, y_pred_lr, acc_lr),
    }
    best_name, (best_model, best_pred, best_acc) = max(
        candidates.items(), key=lambda x: x[1][2]
    )

    print("\nAccuracy:")
    print("Random Forest Accuracy:", acc_rf)
    print("Decision Tree Accuracy:", acc_dt)
    print("Logistic Regression Accuracy:", acc_lr)

    print(f"\nBest Model: {best_name} ({best_acc:.3f})")
    print("\nBest Model Report:\n", classification_report(y_test, best_pred))

    joblib.dump(
        {
            "model": best_model,
            "label_encoder": le,
            "feature_columns": feature_cols,
            "best_model_name": best_name,
        },
        "stress_model.pkl",
    )
    print("Saved best trained model to stress_model.pkl")


if __name__ == "__main__":
    main()
