import os

from _android import setup_android_env
from _shutil import call_echo, get_files, yes
from _script import run_script

if __name__ == "__main__":
    project_dir = r"{{_DIR}}"
    setup_android_env()
    out_apk = project_dir + ".apk"
    call_echo(["apktool", "b", project_dir, "-o", out_apk])

    # must sign the apk in order to install it
    run_script("sign_apk", [out_apk])
