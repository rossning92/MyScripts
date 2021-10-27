import os
import sys
import tempfile
import time


class FileLock:
    def __init__(self, name) -> None:
        self.fh = None
        self.name = name

    def __enter__(self):
        while True:
            lock_file = os.path.join(tempfile.gettempdir(), "filelock_%s" % self.name)
            if sys.platform == "win32":
                try:
                    if os.path.exists(lock_file):
                        os.unlink(lock_file)
                    self.fh = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                    break
                except EnvironmentError as err:
                    if err.errno == 13:
                        time.sleep(0.1)
                    else:
                        raise
                except FileExistsError:
                    time.sleep(0.1)
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
        os.close(self.fh)
