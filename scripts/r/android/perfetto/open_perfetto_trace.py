import sys

from _perfetto import open_trace_in_browser

open_trace_in_browser(sys.argv[-1])
