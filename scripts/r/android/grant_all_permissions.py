import os
import re
import subprocess

from _shutil import setup_logger


def grant_all_permissions(pkg):
    out = subprocess.check_output(
        ["adb", "shell", "dumpsys package com.termux"], universal_newlines=True
    )
    permissions = re.findall(r"(android\.permission\.[A-Z_]+)", out)
    permissions = set(permissions)

    with open(os.devnull, "w") as fnull:
        for permission in permissions:
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
                logger.warn("Failed to grant permission: %s" % permission)


logger = setup_logger()
grant_all_permissions(os.environ.get("PKG_NAME"))
