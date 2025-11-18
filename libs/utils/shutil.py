import logging
import os
import subprocess
import sys

from .process import start_process


def shell_open(file="."):
    logging.debug("shell_open(): %s" % file)
    if sys.platform == "win32":
        file = file.replace("/", os.path.sep)
        os.startfile(file)

    elif sys.platform == "darwin":
        subprocess.Popen(["open", file])

    else:
        try:
            start_process(["xdg-open", file])
        except OSError:
            # er, think of something else to try
            # xdg-open *should* be supported by recent Gnome, KDE, Xfce
            pass
