import subprocess
import os
from colorama import init
from colorama import Fore, Back, Style

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
    pkg_name = pkgs[i]
    print(Fore.LIGHTYELLOW_EX + '(%d / %d) Backup %s ...' % (i + 1, total, pkg_name) + Fore.RESET)

    if os.path.exists('%s.apk' % pkg_name):
        continue

    # Get apk path
    out = subprocess.check_output('adb shell pm path %s' % pkg_name)
    apk_path = out.decode().strip().replace('package:', '')

    # Pull
    subprocess.call('adb pull %s %s.apk' % (apk_path, pkg_name))
