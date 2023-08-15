import argparse
import os

import matplotlib.pyplot as plt
from _math import save_fig
from perfetto.trace_processor import TraceProcessor

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", help="Perfetto trace file")
    args = parser.parse_args()

    processor = TraceProcessor(trace=args.trace)

    name = os.environ["SLICE_NAME"]
    result = processor.query("select dur from slice where name='%s'" % name)
    df = result.as_pandas_dataframe()
    df = df / 1000 / 1000
    print(df)
    avg = df.values.flatten()[0]
    print(df["dur"].describe())

    # Plot stage
    plt.hist(
        df["dur"],
        bins=100,
    )

    plt.legend(loc="upper right")
    plt.xlabel("ms")
    save_fig(f"Histogram of {name}")
