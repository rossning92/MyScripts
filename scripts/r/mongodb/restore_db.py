import glob
import os
import subprocess
import sys

from utils.menu import Menu

if __name__ == "__main__":
    os.chdir(os.environ["MONGODB_BACKUP_DIR"])

    files = sorted(glob.glob("*.gz"))
    menu = Menu(items=files)
    menu.exec()
    backup_file = menu.get_selected_item()
    if backup_file is None:
        print("ERROR: No file is selected, exiting.")
        sys.exit(1)

    print(f"Restore database from '{backup_file}'")
    subprocess.check_call(
        ["mongorestore", "--drop", "--gzip", f"--archive={backup_file}"]
    )
