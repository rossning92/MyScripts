import argparse

import pandas as pd

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compute average value of a column in a CSV file"
    )
    parser.add_argument("--csv", type=str, help="Path to the CSV file")
    parser.add_argument("--col", type=str, help="Name of the column")
    args = parser.parse_args()

    data = pd.read_csv(args.csv)
    mean = data[args.col].mean()
    std = data[args.col].std()
    print(f"{args.csv},{mean},{std}")
