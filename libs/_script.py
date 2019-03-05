import os
import sys
import subprocess
import json
import jinja2
import re
import tempfile
import yaml
import platform
import ctypes
from _shutil import run_elevated, conemu_wrap_args
import shlex
import glob
import locale


def bash(cmd, wsl=False):
    if os.name == 'nt':
        if wsl:  # WSL (Windows Subsystem for Linux)
            if not os.path.exists(r'C:\Windows\System32\bash.exe'):
                raise Exception('WSL (Windows Subsystem for Linux) is not installed.')
            return ['bash.exe', '-c', cmd]
        else:
            return [r'C:\Program Files\Git\bin\bash.exe',
                    '--login',
                    '-i',
                    '-c',
                    cmd]
    elif os.name == 'posix':  # MacOSX
        return ['bash', '-c', cmd]
    else:
        raise Exception('Non supported OS version')


def cmd(cmd):
    assert os.name == 'nt'
    file_name = write_temp_file(cmd, '.cmd')
    args = ['cmd.exe', '/c', file_name]
    return args


def _args_to_str(args):
    if platform.system() == 'windows':
        args = ['"%s"' % a if ' ' in a else a for a in args]
    else:
        args = [shlex.quote(x) for x in args]
    return ' '.join(args)


def write_temp_file(text, ext):
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp:
        temp.write(text.encode('utf-8'))
        return temp.name


def get_variable_file():
    file = os.path.abspath(os.path.dirname(__file__) + '/../variables.' + platform.node() + '.json')
    return file


def get_arg(name):
    with open(get_variable_file(), 'r') as f:
        variables = json.load(f)
    return variables[name][-1]


def get_python_path(script_path):
    python_path = []

    if True:  # Add path directories to python path
        script_root_path = os.path.dirname(__file__) + '/../scripts'
        script_root_path = os.path.abspath(script_root_path)
        script_full_path = os.path.join(os.getcwd(), script_path)
        parent_dir = os.path.dirname(script_full_path)
        python_path.append(parent_dir)
        while True:
            parent_dir = os.path.abspath(parent_dir + '/../')
            if parent_dir.startswith(script_root_path):
                python_path.append(parent_dir)
            else:
                break

    python_path.append(os.path.dirname(__file__))
    return python_path


class ScriptItem:
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath="./"))

    def __str__(self):
        return self.name

    def __init__(self, script_path):
        self.return_code = 0

        # BUG: jinja2 doesn't support '\' in path
        script_path = script_path.replace('\\', '/')
        self.script_path = script_path

        name, ext = os.path.splitext(script_path)
        name = re.sub(r'scripts[\\/]', '', name)  # strip starting scripts/
        name = name.replace('\\', '/')
        self.name = name

        self.ext = ext

        # Load meta
        self.meta = get_script_meta(self.script_path)

        self.override_variables = None

    def render(self):
        with open(self.script_path, 'r', encoding='utf-8') as f:
            source = f.read()
        template = ScriptItem.env.from_string(source)
        ctx = {
            'include': ScriptItem.include.__get__(self, ScriptItem),
            **self.get_variables()
        }
        script = template.render(ctx)
        return script

    def set_override_variables(self, variables):
        self.override_variables = variables

    def get_variables(self):
        if not os.path.isfile(get_variable_file()):
            return {}

        variables = {}
        with open(get_variable_file(), 'r') as f:
            variables = json.load(f)

        # Let only last modified value
        variables = {k: (v[-1] if len(v) > 0 else '') for k, v in variables.items()}

        # Override variables
        if self.override_variables:
            variables = {**variables, **self.override_variables}

        # HACK: Convert to unix path
        if self.ext == '.sh':
            variables = {k: _convert_to_unix_path(v) for k, v in variables.items()}

        return variables

    def execute(self, args=None, control_down=False):
        if args is None:
            args = []
        elif type(args) == str:
            args = [args]

        env = os.environ.copy()
        cwd = os.path.abspath(os.path.join(os.getcwd(), os.path.dirname(self.script_path)))

        if self.ext == '.ps1':
            if os.name == 'nt':
                script = self.render()
                file_path = write_temp_file(script, '.ps1')
                args = ['PowerShell.exe', '-NoProfile',
                        '-ExecutionPolicy', 'unrestricted',
                        file_path]

        elif self.ext == '.ahk':
            if os.name == 'nt':
                # HACK: add python path to env var
                env['PYTHONPATH'] = os.path.dirname(__file__)

                script_abs_path = os.path.join(os.getcwd(), self.script_path)
                subprocess.Popen(
                    ['bin/AutoHotkeyU64.exe', script_abs_path],
                    cwd=cwd, env=env)

        elif self.ext == '.cmd':
            if os.name == 'nt':
                script = self.render()
                args = cmd(script)

                # HACK: change working directory
                if sys.platform == 'win32' and self.meta['runAsAdmin']:
                    args = ['cmd', '/c',
                            'cd', '/d', cwd, '&'] + args

        elif self.ext == '.sh':
            script = self.render()
            args = bash(script, wsl=self.meta['wsl'])

        elif self.ext == '.py':
            script = self.render()
            tmp_script_file = write_temp_file(script, '.py')

            python_path = get_python_path(self.script_path)

            env['PYTHONPATH'] = os.pathsep.join(python_path)
            env['PYTHONDONTWRITEBYTECODE'] = '1'

            if os.name == 'posix':
                args = [sys.executable, tmp_script_file] + args
            else:
                args = [sys.executable, tmp_script_file] + args

            if sys.platform == 'win32' and self.meta['runAsAdmin']:  # HACK: win32 run as admin
                args = ['cmd', '/c',
                        'cd', '/d', cwd, '&',
                        'set', 'PYTHONPATH=' + ';'.join(python_path), '&',
                        'set', 'PYTHONDONTWRITEBYTECODE=1', '&'
                        ] + args

        else:
            print('Not supported script:', self.ext)

        # Set selected file and current folder to as environment variables
        if args is not None and self.meta['autoRun'] is False:
            try:
                with open(os.path.join(os.environ['TEMP'], 'ExplorerInfo.json')) as f:
                    jsn = json.load(f)

                if len(jsn['selectedFiles']) == 1:
                    env['SELECTED_FILE'] = jsn['selectedFiles'][0]
                elif len(jsn['selectedFiles']) > 1:
                    env['SELECTED_FILES'] = '|'.join(jsn['selectedFiles'])

                if jsn['currentFolder']:
                    env['CURRENT_FOLDER'] = jsn['currentFolder']
            except:
                print('Unable to get explorer info.')

        # Run commands
        if args is not None and len(args) > 0:

            # Check if new window is needed
            new_window = self.meta['newWindow'] or control_down
            if new_window:
                try:
                    args = conemu_wrap_args(args, title=self.name, cwd=cwd)
                except:
                    if os.path.exists(r'C:\Program Files\Git\usr\bin\mintty.exe'):
                        args = [r"C:\Program Files\Git\usr\bin\mintty.exe", '--hold', 'always'] + args

            # Check if run as admin
            if self.meta['runAsAdmin']:
                print('Run elevated:', _args_to_str(args))
                run_elevated(args, wait=not new_window)
            else:
                if new_window:
                    subprocess.Popen(args, env=env, cwd=cwd)
                else:
                    self.return_code = subprocess.call(args, env=env, cwd=cwd)

    def get_variable_names(self):
        variables = set()
        include_func = ScriptItem.include.__get__(self, ScriptItem)

        class MyContext(jinja2.runtime.Context):
            def resolve(self, key):
                if key == 'include':
                    return include_func
                variables.add(key)

        ScriptItem.env.context_class = MyContext
        self.render()
        ScriptItem.env.context_class = jinja2.runtime.Context
        return list(variables)

    def include(self, script_name):
        script_path = find_script(script_name, os.path.dirname(self.script_path))
        if script_path is None:
            raise Exception('Cannot find script: %s' % script_name)
        # script_path = os.path.dirname(self.script_path) + '/' + script_path
        return ScriptItem(script_path).render()


def find_script(script_name, search_dir=None):
    if search_dir:
        script_name = os.path.join(search_dir, script_name)

    if os.path.exists(script_name):
        return script_name

    for f in glob.glob(script_name + '*'):
        if os.path.isdir(f):
            continue

        if os.path.splitext(f)[1] == '.yaml':
            continue

        print(os.path.abspath(f))
        return os.path.abspath(f)

    return None


def run_script(script_name, variables=None, new_window=False):
    print('\n>>> RunScript: %s' % script_name)
    script_path = find_script(script_name)
    if script_path is None:
        raise Exception('[ERROR] Cannot find script: "%s"' % script_name)

    script = ScriptItem(script_path)
    script.meta['newWindow'] = new_window

    # Set console window title (for windows only)
    if platform.system() == 'Windows':
        # Save previous title
        MAX_BUFFER = 260
        saved_title = (ctypes.c_char * MAX_BUFFER)()
        res = ctypes.windll.kernel32.GetConsoleTitleA(saved_title, MAX_BUFFER)

        win_title = script.name.encode(locale.getpreferredencoding())
        ctypes.windll.kernel32.SetConsoleTitleA(win_title)

    if variables:
        script.set_override_variables(variables)

    script.execute()
    if script.return_code != 0:
        raise Exception('[ERROR] %s returns %d' % (script_name, script.return_code))

    # Restore title
    if platform.system() == 'Windows':
        ctypes.windll.kernel32.SetConsoleTitleA(saved_title)


def _convert_to_unix_path(path):
    patt = r'^[a-zA-Z]:\\(((?![<>:"/\\|?*]).)+((?<![ .])\\)?)*$'
    if re.match(patt, path):
        path = re.sub(r'^([a-zA-Z]):', lambda x: ('/' + x.group(0)[0].lower()), path)
        path = path.replace('\\', '/')
    return path


class ScriptMeta:
    def __init__(self, script_path):
        self.meta = {
            'hotkey': None,
            'globalHotkey': None,
            'newWindow': False,
            'runAsAdmin': False,
            'autoRun': False,
            'wsl': False
        }

        self.meta_file = os.path.splitext(script_path)[0] + '.yaml'
        default_meta_file = os.path.join(os.path.dirname(script_path), 'default.yaml')

        obj = None
        if os.path.exists(self.meta_file):
            obj = yaml.load(open(self.meta_file, 'r').read())

        elif os.path.exists(default_meta_file):
            obj = yaml.load(open(default_meta_file, 'r').read())

        if obj:
            # override default config
            if obj is not None:
                for k, v in obj.items():
                    self.meta[k] = v

    def save(self):
        yaml.dump(self.meta, open(self.meta_file, 'w'), default_flow_style=False)


def get_script_meta(script_path):
    return ScriptMeta(script_path).meta
