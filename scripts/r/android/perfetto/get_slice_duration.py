import os

from _shutil import cd
from perfetto.trace_processor import TraceProcessor

if __file__ == "__main__":
    cd(r"C:\tmp")

    processor = TraceProcessor(trace="trace")

    name = os.environ["SLICE_NAME"]
    result = processor.query(
        "select avg(dur), min(dur), max(dur) from slice where name='%s'" % name
    )
    df = result.as_pandas_dataframe()
    df = df / 1000 / 1000
    avg = df.values.flatten()[0]
    print(avg)
