from _shutil import *
from utils.android import *

# https://uwot.eu/blog/manually-backuprestore-android-applications-data/


out_dir = os.path.realpath(os.path.expanduser("~/Desktop/android_backup"))
mkdir(out_dir)
cd(out_dir)

# Get all package names
out = subprocess.check_output("adb shell pm list packages -3")
out = out.decode("utf-8")
lines = out.split("\n")
lines = [x.strip() for x in lines if x]
pkgs = [x.replace("package:", "") for x in lines]

pprint(pkgs)
save_config("user_apps", pkgs)
