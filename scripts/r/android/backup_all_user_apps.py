import subprocess
import os
from colorama import init
from colorama import Fore, Back, Style
import re
from _android import *

# https://uwot.eu/blog/manually-backuprestore-android-applications-data/

init()

out_dir = os.environ['USERPROFILE'] + '\\Desktop\\android_backup'
if not os.path.exists(out_dir):
    os.mkdir(out_dir)
os.chdir(out_dir)

# Get all package names
out = subprocess.check_output('adb shell pm list packages -3')
out = out.decode('utf-8')
lines = out.split('\n')
lines = [x.strip() for x in lines if x]
pkgs = [x.replace('package:', '') for x in lines]

# For each package
total = len(pkgs)
for i in range(total):
    pkg = pkgs[i]
    print(Fore.LIGHTYELLOW_EX + '(%d / %d) Backup %s ...' % (i + 1, total, pkg) + Fore.RESET)

    # Skip existing apk
    if os.path.exists('%s.apk' % pkg):
        continue

    backup_pkg(pkg)
