import subprocess
import sys
from typing import List


def start_process(args: List[str], shell=False):
    if sys.platform == "win32":
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        DETACHED_PROCESS = 0x00000008
        creationflags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        start_new_session = False
        close_fds = False
    else:
        creationflags = 0
        start_new_session = True
        close_fds = True

    subprocess.Popen(
        args,
        shell=shell,
        creationflags=creationflags,
        start_new_session=start_new_session,
        stdin=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        close_fds=close_fds,
    )
