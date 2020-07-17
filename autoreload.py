#!/usr/bin/env python
import glob
import os
import signal
import subprocess
import sys
import time


def handler(signum, frame):
    pass


# Set the signal handler
signal.signal(signal.SIGINT, handler)


def get_mtime():
    for filename in glob.iglob("*.py"):
        yield os.stat(filename).st_mtime


command = [sys.executable, "main_console.py"]

# How often we check the filesystem for changes (in seconds)
WAIT = 1

# The process to autoreload
process = subprocess.Popen(command)

# The current maximum file modified time under the watched directory
last_mtime = max(get_mtime())


while True:
    try:
        max_mtime = max(get_mtime())
        # print_stdout(process)
        if max_mtime > last_mtime:
            last_mtime = max_mtime
            process.kill()
            process = subprocess.Popen(command)
        
        ret = process.poll()
        if ret is not None:
            if ret != 0:
                input("press enter to continue...")
            process = subprocess.Popen(command)

        time.sleep(WAIT)
    except KeyboardInterrupt:
        process.kill()
        process = subprocess.Popen(command)
