from _android import setup_android_env
from _shutil import get_files, call_echo, yes

if __name__ == "__main__":
    f = get_files(cd=True)[0]
    setup_android_env()
    call_echo(["apktool", "decode", "-f", f])  # override
