import argparse
import os

import pandas as pd
from perfetto.trace_processor import TraceProcessor

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", help="Perfetto trace file")
    parser.add_argument(
        "--name", help="Slice name to analyze", default=os.environ.get("SLICE_NAME")
    )
    args = parser.parse_args()

    processor = TraceProcessor(trace=args.trace)

    name = args.name
    result = processor.query("select dur from slice where name='%s'" % args.name)
    df = result.as_pandas_dataframe()
    df["dur"] = pd.to_numeric(df["dur"], errors="coerce")
    df = df / 1000 / 1000
    print(df["dur"].describe())
