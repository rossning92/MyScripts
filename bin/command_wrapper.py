import os
import subprocess
import sys
import time

LONG_RUNNING_SCRIPT_SECS = 10

if __name__ == "__main__":
    close_on_exit = int(os.environ.get("CLOSE_ON_EXIT", "1"))

    start_time = time.time()
    args = sys.argv[1:]
    code = subprocess.call(args)
    end_time = time.time()

    has_error = code != 0
    duration = end_time - start_time
    keep_terminal_on = not close_on_exit
    if has_error or keep_terminal_on:
        print("---")
        print("(exit code: %d)" % code)
        print("(duration: %.2f seconds)" % duration)
        print("(cmdline: %s)" % args)
        input()
