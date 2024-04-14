import logging
import os
import re
import subprocess
from typing import Set

from utils.logger import setup_logger


def grant_all_permissions(pkg):
    out = subprocess.check_output(
        ["adb", "shell", "dumpsys package %s" % pkg], universal_newlines=True
    )
    permissions: Set[str] = set(re.findall(r"(android\.permission\.[A-Z_]+)", out))

    with open(os.devnull, "w") as fnull:
        for permission in permissions:
            print("Grant %s" % permission)
            ret_code = subprocess.call(
                [
                    "adb",
                    "shell",
                    "pm grant %s %s" % (pkg, permission),
                ],
                stderr=fnull,
                stdout=fnull,
            )
            if ret_code != 0:
                logging.warning("Failed to grant permission: %s" % permission)


if __name__ == "__main__":
    setup_logger()
    grant_all_permissions(os.environ.get("PKG_NAME"))
