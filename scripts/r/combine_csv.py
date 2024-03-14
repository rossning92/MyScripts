import argparse
import os
import tempfile

import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("directory", help="Directory to parse CSV files from")
args = parser.parse_args()

directory = args.directory
combined_data = pd.DataFrame()

for filename in os.listdir(directory):
    if filename.endswith(".csv"):
        filepath = os.path.join(directory, filename)
        data = pd.read_csv(filepath)
        combined_data = pd.concat([combined_data, data])

combined_data.drop_duplicates(subset=["address"], inplace=True)

tmpdir = tempfile.gettempdir()
combined_data.to_csv(os.path.join(tmpdir, "output.csv"), index=False)
