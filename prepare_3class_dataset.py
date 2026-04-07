import argparse
import numpy as np
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a 3-class stress dataset")
    parser.add_argument("--input", default="synthetic_stress_data.csv", help="Input CSV path")
    parser.add_argument(
        "--output",
        default="synthetic_stress_data_3class.csv",
        help="Output CSV path",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input)

    if "stress" not in df.columns:
        raise ValueError("Input dataset must contain a 'stress' column")

    if df["stress"].isna().any():
        raise ValueError("Input dataset contains missing values in 'stress'")

    # Ensure all three classes exist for viva/demo purposes.
    conditions = [
        df["stress"] < 300,
        (df["stress"] >= 300) & (df["stress"] < 450),
        df["stress"] >= 450,
    ]
    labels = ["Normal", "Warning", "Critical"]
    df["label"] = np.select(conditions, labels, default="Warning")

    df.to_csv(args.output, index=False)

    print("Saved:", args.output)
    print("Label distribution:")
    print(df["label"].value_counts())


if __name__ == "__main__":
    main()
