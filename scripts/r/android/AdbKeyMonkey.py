import os
import subprocess

from _shutil import download, get_home_path
from utils.android import setup_android_env

if __name__ == "__main__":
    install_path = os.path.join(get_home_path(), "tools", "AdbKeyMonkey")
    os.makedirs(install_path, exist_ok=True)
    os.chdir(install_path)
    download(
        "https://github.com/ckesc/AdbKeyMonkey/releases/download/v1.0.4/AdbKeyMonkey-1.0.4.jar"
    )

    setup_android_env()

    subprocess.call(
        ["java", "-jar", "AdbKeyMonkey-1.0.4.jar"], close_fds=True, shell=True
    )
