from _android import *
from _shutil import *

out_dir = os.path.realpath(os.path.expanduser("~/Desktop/android_backup"))
cd(out_dir)

pkgs = load_config("user_apps")

# For each package
total = len(pkgs)
for i in range(total):
    pkg = pkgs[i]
    print2("(%d / %d) Backup %s ..." % (i + 1, total, pkg))

    # Skip existing apk
    if os.path.exists("%s.apk" % pkg):
        continue

    backup_pkg(pkg)
