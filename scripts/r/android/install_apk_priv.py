import os

from _android import adb_shell
from _shutil import call2, get_files


def adb_install_priv_app(apk):
    basename, _ = os.path.splitext(os.path.basename(apk))
    call2(["adb", "root"])
    call2(["adb", "remount"])
    adb_shell("mkdir -p /system/priv-app/%s" % basename)

    dst = "/system/priv-app/%s/" % basename
    call2(["adb", "push", apk, dst])
    adb_shell("chown -R root %s" % dst)
    adb_shell("chmod 644 %s" % dst)


files = get_files()

for file in files:
    assert os.path.splitext(file)[1].lower() == ".apk"

    print("Installing apk: %s" % file)
    adb_install_priv_app(file)
