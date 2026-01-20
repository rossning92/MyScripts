from _shutil import *
from utils.android import *
from utils.jsonutil import load_json

out_dir = os.path.realpath(os.path.expanduser("~/Desktop/android_backup"))
cd(out_dir)

pkgs = load_json("user_apps.json")

# For each package
total = len(pkgs)
for i in range(total):
    pkg = pkgs[i]

    # Skip existing apk
    if os.path.exists(os.path.join("apk", "%s.apk" % pkg)):
        continue

    print2("(%d / %d) Backup %s ..." % (i + 1, total, pkg))
    backup_pkg(pkg, out_dir="apk")


adb_tar("/sdcard/data/com.teslacoilsw.launcher/backup", "nova_backup.tar")
