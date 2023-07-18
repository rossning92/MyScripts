import argparse
import os

from perfetto.trace_processor import TraceProcessor

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", help="Perfetto trace file")
    parser.add_argument(
        "--sql",
        default=None,
        type=str,
    )
    args = parser.parse_args()

    processor = TraceProcessor(
        trace=args.file,
    )

    with open(args.sql, "r", encoding="utf-8") as f:
        result = processor.query(f.read())
    df = result.as_pandas_dataframe()
    print(df)
    out_csv_file = os.path.splitext(args.file)[0] + ".csv"
    df.to_csv(out_csv_file, index=None)
