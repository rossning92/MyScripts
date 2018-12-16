import _script
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


def export_python(script_path):
    with open(script_path, 'r') as f:
        content = f.read()

    # Find imports dependencies
    module_names = re.findall(r'(?:^from|import) (_[a-zA-Z_]+)', content, flags=re.MULTILINE)
    python_path = _script.get_python_path(script_path)
    for m in module_names:
        python_module = find_module(python_path, m)
        assert (python_module is not None)

        print('Copy: %s' % python_module)
        shutil.copy(python_module, OUT_DIR)

        # Find dependencies recursively
        export_python(python_module)

    # Find dependencies to other scripts
    other_scripts = re.findall(r'(?<=\W)(?:(?:\w+|\.\.)/)*\w+\.(?:py|cmd|ahk|sh)(?=\W)', content)
    for s in other_scripts:
        s = os.path.abspath(os.path.dirname(script_path) + '/' + s)
        if os.path.exists(s):
            shutil.copy(s, '%s/%s' % (OUT_DIR, os.path.basename(s)))
            print('Copy: %s' % s)

    out_file = '%s/%s' % (OUT_DIR, os.path.basename(script_path))
    if os.path.basename(script_path).startswith('_'):
        shutil.copy(script_path, out_file)
    else:
        print('Render script: %s' % script_path)
        with open(out_file, 'w') as f:
            f.write(_script.ScriptItem(script_path).render())


if os.path.splitext(script_path)[1].lower() == '.py':
    export_python(script_path)
