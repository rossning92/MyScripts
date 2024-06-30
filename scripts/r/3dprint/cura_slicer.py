import os
import shutil
import subprocess
import sys

from _shutil import download

if sys.platform == "linux":
    cura_exec = os.path.expanduser(
        "~/Downloads/UltiMaker-Cura-5.6.0-linux-X64.AppImage"
    )
    cura_setting_dir = os.path.expanduser("~/.config/cura/5.6")

    download(
        "https://github.com/Ultimaker/Cura/releases/download/5.6.0/UltiMaker-Cura-5.6.0-linux-X64.AppImage",
        filename=cura_exec,
    )
    os.chmod(cura_exec, 0o755)

elif sys.platform == "win32":
    cura_setting_dir = os.path.expandvars(r"%APPDATA%\cura\5.1")
    cura_exec = r"C:\Program Files\Ultimaker Cura 5.1.0\Ultimaker-Cura.exe"

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    if os.environ.get("CURA_RESTORE_SETTING"):
        shutil.unpack_archive("cura_settings.zip", cura_setting_dir)

    subprocess.call([cura_exec])

    if os.environ.get("CURA_BACKUP_SETTING"):
        shutil.make_archive("cura_settings", "zip", cura_setting_dir)
