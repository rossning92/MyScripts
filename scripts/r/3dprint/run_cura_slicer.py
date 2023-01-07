import os
import shutil
import subprocess

CURA_SETTING_DIR = os.path.expandvars(r"%APPDATA%\cura\5.1")
CURA_EXEC = r"C:\Program Files\Ultimaker Cura 5.1.0\Ultimaker-Cura.exe"

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    if os.environ.get("_RESTORE_SETTING"):
        shutil.unpack_archive("cura_settings.zip", CURA_SETTING_DIR)

    subprocess.call([CURA_EXEC])

    if os.environ.get("_BACKUP_SETTING"):
        shutil.make_archive("cura_settings", "zip", CURA_SETTING_DIR)
