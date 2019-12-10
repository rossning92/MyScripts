from _shutil import *
from _android import *
from _gui import *

setup_android_env()

cd('~/Desktop/android_backup')

apk_list = glob.glob('*.apk')

app_names = []
for f in apk_list:
    s = subprocess.check_output(['aapt', 'dump', 'badging', f]).decode(errors='replace')
    m = re.search("application-label:'(.*?)'", s)
    if not m:
        label = ''
    else:
        label = m.group(1)

    name = '%s - %s' % (label, f)
    print(name)
    app_names.append(name)

indices = select_options(app_names)
for n in indices:
    f = apk_list[n]
    name_no_ext = os.path.splitext(f)[0]
    print2('Delete %s.*' % name_no_ext)
    remove(name_no_ext + '.*')
