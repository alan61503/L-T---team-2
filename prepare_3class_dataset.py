import argparse
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

    # Ensure all three classes exist for viva/demo purposes.
    conditions = [
        df["stress"] < 300,
        (df["stress"] >= 300) & (df["stress"] < 450),
        df["stress"] >= 450,
    ]
    labels = ["Normal", "Warning", "Critical"]
    df["label"] = pd.Series(pd.NA, index=df.index)
    df.loc[conditions[0], "label"] = labels[0]
    df.loc[conditions[1], "label"] = labels[1]
    df.loc[conditions[2], "label"] = labels[2]

    df.to_csv(args.output, index=False)

    print("Saved:", args.output)
    print("Label distribution:")
    print(df["label"].value_counts())


if __name__ == "__main__":
    main()
