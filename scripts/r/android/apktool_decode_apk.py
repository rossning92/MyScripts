from _shutil import call_echo, get_files
from utils.android import setup_android_env

if __name__ == "__main__":
    f = get_files(cd=True)[0]
    setup_android_env()
    call_echo(["apktool", "decode", "-f", f])  # override
