import myutils
import os
import re
import shutil

OUT_DIR = os.path.expanduser('~/Desktop/ScriptExport')
os.makedirs(OUT_DIR, exist_ok=True)

script = os.getenv('ROSS_SELECTED_SCRIPT_PATH')

with open(script, 'r') as f:
    s = f.read()

module_names = re.findall('(?:^from|import) (_[a-zA-Z_]+)', s, flags=re.MULTILINE)
python_path = myutils.get_python_path(script)


def find_module(module):
    for p in python_path:
        path = os.path.join(p, module + '.py')
        if os.path.exists(path):
            return path
    return None


for m in module_names:
    python_file = find_module(m)
    assert (python_file is not None)

    print('Copy %s ...' % python_file)
    shutil.copy(python_file, OUT_DIR)

print('Copy %s ...' % script)
shutil.copy(script, OUT_DIR)
