from _android import *

# https://uwot.eu/blog/manually-backuprestore-android-applications-data/


cd('~/Desktop/android_backup')

installed_pkgs = set(pm_list_packages())

apk_list = list(glob.glob('*.apk'))
total = len(apk_list)
for i, f in enumerate(apk_list):
    pkg_name = os.path.splitext(f)[0]
    print2('(%d / %d) Restore %s ...' % (i + 1, total, f), color='green')

    if pkg_name not in installed_pkgs:
        adb_install2(f)
    else:
        print2('%s already installed.' % pkg_name)
