import os
import sys

from backup_app import select_app_pkg
from utils.android import backup_pkg, select_app_pkg
from utils.shutil import shell_open

if __name__ == "__main__":
    pkg = os.environ.get("PKG_NAME")
    if not pkg:
        pkg = select_app_pkg()
    if not pkg:
        print("ERROR: pkg cannot be empty.")
        sys.exit(1)

    out_dir = os.environ["ANDROID_APP_BACKUP_DIR"]
    os.makedirs(out_dir, exist_ok=True)
    backup_pkg(
        pkg, out_dir=out_dir, backup_apk=False, backup_user_data=True, backup_obb=False
    )
    shell_open(out_dir)
