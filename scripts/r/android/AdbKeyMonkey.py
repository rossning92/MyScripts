import subprocess

from _android import setup_android_env
from _shutil import cd, download

cd("C:\\tools")
download(
    "https://github.com/ckesc/AdbKeyMonkey/releases/download/v1.0.4/AdbKeyMonkey-1.0.4.jar"
)

setup_android_env()

subprocess.call(["java", "-jar", "AdbKeyMonkey-1.0.4.jar"], close_fds=True, shell=True)
