import logging
import os
import subprocess
import sys


def start_process(args, shell=False):
    creationflags = 0
    if sys.platform == "win32":
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        DETACHED_PROCESS = 0x00000008
        creationflags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP

    if sys.platform == "linux":
        start_new_session = True
    else:
        start_new_session = False

    subprocess.Popen(
        args,
        shell=shell,
        creationflags=creationflags,
        start_new_session=start_new_session,
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
    )


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
