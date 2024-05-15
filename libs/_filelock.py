import os
import sys
import tempfile
import time
from io import TextIOWrapper
from typing import Optional


class FileLock:
    def __init__(self, name) -> None:
        self.fh: Optional[TextIOWrapper] = None
        self.name = name

    def __enter__(self):
        while True:
            lock_file = os.path.join(tempfile.gettempdir(), "filelock_%s" % self.name)
            if sys.platform == "win32":
                try:
                    if os.path.exists(lock_file):
                        os.remove(lock_file)
                    self.fh = open(lock_file, "x")
                    break
                except FileExistsError:
                    time.sleep(0.1)
                except EnvironmentError as err:
                    if err.errno == 13:
                        time.sleep(0.1)
                    else:
                        raise

            else:
                import fcntl

                try:
                    self.fh = open(lock_file, "w")
                    fcntl.lockf(self.fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except EnvironmentError as err:
                    if self.fh is not None:
                        time.sleep(0.1)
                    else:
                        raise

        return self.fh

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self.fh is not None
        self.fh.close()
