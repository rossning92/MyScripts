import _script
import os
import re
import shutil
from os.path import splitext, join, basename, expanduser, exists, abspath, dirname, sep
import subprocess

OUT_DIR = expanduser('~/Desktop/ScriptExport')
os.makedirs(OUT_DIR, exist_ok=True)

script_path = os.getenv('ROSS_SELECTED_SCRIPT_PATH')


def find_module(python_path, module):
    for p in python_path:
        path = join(p, module + '.py')
        if exists(path):
            return path
    return None


def export_python(script_path):
    with open(script_path, 'rb') as f:
        content = f.read()

    # Find imports dependencies
    module_names = re.findall(rb'(?:^from|import) (_[a-zA-Z_]+)', content, flags=re.MULTILINE)
    python_path = _script.get_python_path(script_path)
    for m in module_names:
        m = m.decode()
        python_module = find_module(python_path, m)
        assert (python_module is not None)

        print('Copy: %s' % python_module)
        shutil.copy(python_module, OUT_DIR)

        # Find dependencies recursively
        export_python(python_module)


def export_script(script_path):
    with open(script_path, 'r') as f:
        content = f.read()

    # Find dependencies to other scripts
    old_new_path_map = {}
    other_scripts = re.findall(r'(?<=\W)(?:(?:\w+|\.\.)/)*\w+\.(?:py|cmd|ahk|sh)(?=\W)', content)
    for s in other_scripts:
        script_abs_path = abspath(dirname(script_path) + '/' + s)
        file_name = basename(script_abs_path)
        if exists(script_abs_path):
            shutil.copy(script_abs_path, '%s/%s' % (OUT_DIR, file_name))
            old_new_path_map[s] = file_name
            print('Copy: %s' % script_abs_path)
            export_script(script_abs_path)  # Recurse

    if splitext(script_path)[1] == '.py':
        export_python(script_path)

        launcher = f'{OUT_DIR}{sep}{splitext(basename(script_path))[0]}.cmd'
        shutil.copy('../../install/find_python.cmd',
                    f'{OUT_DIR}{sep}_find_python.cmd')
        with open(launcher, 'w') as f:
            f.write(f'@call _find_python.cmd\n'
                    f'@python {basename(script_path)}\n')

    # Replace script path
    for k, v in old_new_path_map.items():
        content = content.replace(k, v)

    # Render scripts
    out_file = '%s/%s' % (OUT_DIR, basename(script_path))
    print('Render: %s' % script_path)
    with open(out_file, 'w') as f:
        # _script.ScriptItem(script_path).render()
        f.write(content)

    subprocess.call(f'start "" "{OUT_DIR}"', shell=True)

export_script(script_path)
