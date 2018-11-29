import myutils
import os
import re
import shutil

OUT_DIR = os.path.expanduser('~/Desktop/ScriptExport')
os.makedirs(OUT_DIR, exist_ok=True)

script_path = os.getenv('ROSS_SELECTED_SCRIPT_PATH')


def find_module(python_path, module):
    for p in python_path:
        path = os.path.join(p, module + '.py')
        if os.path.exists(path):
            return path
    return None


def export_python_script(script_path):
    with open(script_path, 'r') as f:
        s = f.read()

    module_names = re.findall('(?:^from|import) (_[a-zA-Z_]+)', s, flags=re.MULTILINE)
    python_path = myutils.get_python_path(script_path)

    for m in module_names:
        python_file = find_module(python_path, m)
        assert (python_file is not None)

        print('Copy %s ...' % python_file)
        shutil.copy(python_file, OUT_DIR)

    print('Write script: %s ...' % script_path)
    with open('%s/%s' % (OUT_DIR, os.path.basename(script_path)), 'w') as f:
        f.write(myutils.ScriptItem(script_path).render())


if os.path.splitext(script_path)[1].lower() == '.py':
    export_python_script(script_path)
