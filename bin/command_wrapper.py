import os
import subprocess
import sys
import time

LONG_RUNNING_SCRIPT_SECS = 10

if __name__ == "__main__":
    close_on_exit = int(os.environ.get("CLOSE_ON_EXIT", "1"))

    start_time = time.time()
    ret = subprocess.call(sys.argv[1:])
    end_time = time.time()

    has_error = ret != 0
    long_running_script = end_time - start_time > LONG_RUNNING_SCRIPT_SECS
    keep_terminal_on = not close_on_exit
    if has_error or long_running_script or keep_terminal_on:
        print("---")
        print("(press enter to exit...)")
        input()
