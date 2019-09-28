import os
import sys
import subprocess
import json
import jinja2
import re
import yaml
import platform
import ctypes
from _shutil import *
import shlex
import glob
import locale


def set_console_title(title):
    if platform.system() == 'Windows':
        old = get_console_title()
        win_title = title.encode(locale.getpreferredencoding())
        ctypes.windll.kernel32.SetConsoleTitleA(win_title)
        return old

    return None


def get_console_title():
    if platform.system() == 'Windows':
        MAX_BUFFER = 260
        saved_title = (ctypes.c_char * MAX_BUFFER)()
        ret = ctypes.windll.kernel32.GetConsoleTitleA(saved_title, MAX_BUFFER)
        assert ret > 0
        return saved_title.value.decode(locale.getpreferredencoding())

    return None


def bash(bash, wsl=False):
    if os.name == 'nt':
        if wsl:  # WSL (Windows Subsystem for Linux)
            if not os.path.exists(r'C:\Windows\System32\bash.exe'):
                raise Exception(
                    'WSL (Windows Subsystem for Linux) is not installed.')
            # Escape dollar sign? Why?
            bash = bash.replace('$', r'\$')
            return ['bash.exe', '-c', bash]
        else:
            return [r'C:\Program Files\Git\bin\bash.exe',
                    '--login',
                    '-i',
                    '-c',
                    bash]
    elif os.name == 'posix':  # MacOSX
        return ['bash', '-c', bash]
    else:
        raise Exception('Non supported OS version')


def exec_cmd(cmd):
    assert os.name == 'nt'
    file_name = write_temp_file(cmd, '.cmd')
    args = ['cmd.exe', '/c', file_name]
    subprocess.check_call(args)


def _args_to_str(args):
    if platform.system() == 'Windows':
        args = ['"%s"' % a if ' ' in a else a for a in args]
    else:
        args = [shlex.quote(x) for x in args]
    return ' '.join(args)


def get_data_folder():
    app_dir = os.path.abspath(os.path.dirname(__file__) + '/../')
    folder = os.path.join(app_dir, 'data', platform.node())
    os.makedirs(folder, exist_ok=True)
    return folder


def get_variable_file():
    variable_file = os.path.join(get_data_folder(), 'variables.json')

    if True:  # Deprecated: copy old variable file to new path
        my_script_dir = os.path.abspath(os.path.dirname(__file__) + '/../')
        variable_file2 = os.path.abspath(
            my_script_dir + '/variables.' + platform.node() + '.json')
        if exists(variable_file2):
            shutil.copy(variable_file2, variable_file)
            os.remove(variable_file2)

    return variable_file


def get_all_variables():
    with open(get_variable_file(), 'r') as f:
        variables = json.load(f)
        return variables


def get_arg(name):
    with open(get_variable_file(), 'r') as f:
        variables = json.load(f)
    return variables[name][-1]


def set_variable(name, val):
    file = get_variable_file()
    with open(file, 'r') as f:
        variables = json.load(f)

    vals = variables[name]
    try:
        vals.remove(val)
    except ValueError:
        pass
    vals.append(val)

    with open(file, 'w') as f:
        json.dump(variables, f, indent=4)


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

    def __init__(self, script_path, name=None):
        self.return_code = 0

        # TODO: jinja2 doesn't support '\' in path. Seems fixed?
        script_path = script_path.replace(os.path.sep, '/')

        self.meta = get_script_meta(script_path)  # Load meta
        self.ext = os.path.splitext(script_path)[
            1].lower()  # Extension / script type
        self.name = name if name else script_path  # Script display name
        self.override_variables = None
        self.console_title = None
        self.script_path = script_path

        # Deal with links
        if os.path.splitext(script_path)[1].lower() == '.link':
            self.real_script_path = open(
                script_path, 'r', encoding='utf-8').read().strip()
            self.real_ext = os.path.splitext(self.real_script_path)[1].lower()
        else:
            self.real_script_path = None
            self.real_ext = None

    def get_console_title(self):
        return self.console_title if self.console_title else self.name

    def render(self):
        script_path = self.real_script_path if self.real_script_path else self.script_path

        with open(script_path, 'r', encoding='utf-8') as f:
            source = f.read()
        template = ScriptItem.env.from_string(source)
        ctx = {
            'include': ScriptItem.include.__get__(self, ScriptItem),
            **self.get_variables()
        }
        return template.render(ctx)

    def set_override_variables(self, variables):
        self.override_variables = variables

    def get_variables(self):
        if not os.path.isfile(get_variable_file()):
            return {}

        variables = {}
        with open(get_variable_file(), 'r') as f:
            variables = json.load(f)

        # Get only last modified value
        variables = {k: (v[-1] if len(v) > 0 else '')
                     for k, v in variables.items()}

        # Override variables
        if self.override_variables:
            variables = {**variables, **self.override_variables}

        # Convert into private namespace (shorter variable name)
        prefix = self.get_public_variable_prefix()
        variables = {
            re.sub('^' + re.escape(prefix) + '_', '_', k): v
            for k, v in variables.items()
        }

        # HACK: Convert to unix path
        if self.ext == '.sh':
            variables = {k: _convert_to_unix_path(
                v) for k, v in variables.items()}

        return variables

    def get_public_variable_prefix(self):
        return os.path.splitext(os.path.basename(self.script_path))[0].upper()

    def execute(self, args=None, control_down=False):
        script_path = self.real_script_path if self.real_script_path else self.script_path
        ext = self.real_ext if self.real_ext else self.ext

        if type(args) == str:
            args = [args]
        elif type(args) == list:
            args = args
        else:
            args = []

        env = {}

        # HACK: pass current folder
        if 'CURRENT_FOLDER' in os.environ:
            env['CURRENT_FOLDER'] = os.environ['CURRENT_FOLDER']

        cwd = os.path.abspath(os.path.join(
            os.getcwd(), os.path.dirname(script_path)))

        if ext == '.ps1':
            if os.name == 'nt':
                if self.meta['template']:
                    ps_path = write_temp_file(self.render(), '.ps1')
                else:
                    ps_path = os.path.realpath(script_path)

                args = ['PowerShell.exe', '-NoProfile',
                        '-ExecutionPolicy', 'unrestricted',
                        ps_path]

        elif ext == '.ahk':
            if os.name == 'nt':
                # HACK: add python path to env var
                env['PYTHONPATH'] = os.path.dirname(__file__)

                script_abs_path = os.path.abspath(script_path)
                args = ['AutoHotkeyU64.exe', script_abs_path]
                self.meta['background'] = True

                if self.meta['runAsAdmin']:
                    args = ['start'] + args

        elif ext == '.cmd' or ext == '.bat':
            if os.name == 'nt':
                if self.meta['template']:
                    batch_file = write_temp_file(self.render(), '.cmd')
                else:
                    batch_file = os.path.realpath(script_path)

                args = ['cmd.exe', '/c', batch_file] + args

                # HACK: change working directory
                if platform.system() == 'Windows' and self.meta['runAsAdmin']:
                    args = ['cmd', '/c',
                            'cd', '/d', cwd, '&'] + args
            else:
                print('OS does not support script: %s' % script_path)
                return

        elif ext == '.sh':
            # TODO: if self.meta['template']:
            args = bash(self.render(), wsl=self.meta['wsl'])

        elif ext == '.py':
            if self.meta['template']:
                python_file = write_temp_file(self.render(), '.py')
            else:
                python_file = os.path.realpath(script_path)

            python_path = get_python_path(script_path)

            env['PYTHONPATH'] = os.pathsep.join(python_path)
            env['PYTHONDONTWRITEBYTECODE'] = '1'

            if self.meta['anaconda']:
                import _conda
                activate = _conda.get_conda_path() + '\\Scripts\\activate.bat'
                args = ['cmd', '/c', activate, '&',
                        'python', python_file] + args

            else:
                python_executable = sys.executable
                args = [python_executable, python_file] + args

        elif ext == '.vbs':
            assert os.name == 'nt'

            script_abs_path = os.path.join(os.getcwd(), script_path)
            args = ['cscript', '//nologo', script_abs_path]

        else:
            print('Not supported script:', ext)

        if self.meta['restartInstance']:
            # Only works on windows for now
            if platform.system() == 'Windows':
                exec_ahk(f'WinClose, {self.get_console_title()}', wait=True)

        # Run commands
        if args is not None and len(args) > 0:
            # Check if new window is needed
            new_window = self.meta['newWindow'] or control_down
            if new_window:

                if sys.platform == 'win32':  # HACK: use python wrapper: activate console window once finished
                    args = [
                        sys.executable, '-c',
                        'import subprocess;'
                        'import ctypes;'
                        f'import sys;sys.path.append(r"{os.path.dirname(__file__)}");'
                        'import _script as s;'
                        f's.set_console_title(r"{self.console_title if self.console_title else self.name}");'
                        f'ret = subprocess.call({args});'
                        'hwnd = ctypes.windll.kernel32.GetConsoleWindow();'
                        'ctypes.windll.user32.SetForegroundWindow(hwnd);'
                        's.set_console_title(s.get_console_title() + " (Finished)");'
                        'sys.exit(ret)'
                    ]

                    try:
                        args = conemu_wrap_args(args, cwd=cwd, small_window=True)
                    except:
                        if os.path.exists(r'C:\Program Files\Git\usr\bin\mintty.exe'):
                            args = [r"C:\Program Files\Git\usr\bin\mintty.exe",
                                    '--hold', 'always'] + args
                    
                elif sys.platform == 'linux':
                    args = ['gnome-terminal', '--'] + args

            # Check if run as admin
            if platform.system() == 'Windows' and self.meta['runAsAdmin']:
                # Set environment variables through command lines
                bin_path = os.path.abspath(
                    os.path.dirname(__file__) + '/../bin')
                set_env_var = []
                for k, v in env.items():
                    set_env_var += ['set', '%s=%s' % (k, v), '&']

                args = ['cmd', '/c',
                        'title', self.name, '&',
                        'cd', '/d', cwd, '&',
                        'set', f'PATH={bin_path};%PATH%', '&'
                        ] + set_env_var + args

                print2('Run elevated:')
                print2(_args_to_str(args), color='cyan')
                run_elevated(args, wait=(not new_window))
            else:
                if new_window or self.meta['background']:
                    # Check whether or not hide window
                    startupinfo = None
                    creationflags = 0
                    if self.meta['background']:
                        if platform.system() == 'Windows':
                            SW_HIDE = 0
                            startupinfo = subprocess.STARTUPINFO()
                            startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
                            startupinfo.wShowWindow = SW_HIDE
                            creationflags = subprocess.CREATE_NEW_CONSOLE

                    subprocess.Popen(args,
                                     env={**os.environ, **env},
                                     cwd=cwd,
                                     startupinfo=startupinfo,
                                     creationflags=creationflags,
                                     close_fds=True)
                else:
                    self.return_code = subprocess.call(
                        args, env={**os.environ, **env}, cwd=cwd)

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

        variables = list(variables)

        # Convert private variable to global namespace
        prefix = self.get_public_variable_prefix()
        variables = [prefix + v if v.startswith('_') else v for v in variables]

        return variables

    def include(self, script_name):
        script_path = find_script(
            script_name, os.path.dirname(self.script_path))
        if script_path is None:
            raise Exception('Cannot find script: %s' % script_name)
        # script_path = os.path.dirname(self.script_path) + '/' + script_path
        return ScriptItem(script_path).render()


def find_script(script_name, search_dir=None):
    if script_name.startswith('/'):
        script_path = os.path.abspath(os.path.dirname(
            __file__) + '/../scripts' + script_name)
    elif search_dir:
        script_path = os.path.join(search_dir, script_name)
    else:
        script_path = os.path.abspath(script_name)

    if os.path.exists(script_path):
        return script_path

    for f in glob.glob(script_path + '*'):
        if os.path.isdir(f):
            continue
        if os.path.splitext(f)[1] == '.yaml':
            continue
        return f

    return None


def run_script(script_name, variables=None, new_window=False, set_console_title=False, console_title=None):
    print2('RunScript: %s' % script_name, color='green')
    script_path = find_script(script_name)
    if script_path is None:
        raise Exception('[ERROR] Cannot find script: "%s"' % script_name)

    script = ScriptItem(script_path)

    # Override meta
    script.meta['newWindow'] = new_window
    script.meta['restartInstance'] = False

    if console_title:
        script.console_title = console_title

    # Set console window title (for windows only)
    if set_console_title and platform.system() == 'Windows':
        # Save previous title
        MAX_BUFFER = 260
        saved_title = (ctypes.c_char * MAX_BUFFER)()
        res = ctypes.windll.kernel32.GetConsoleTitleA(saved_title, MAX_BUFFER)
        win_title = console_title.encode(locale.getpreferredencoding())
        ctypes.windll.kernel32.SetConsoleTitleA(win_title)

    if variables:
        script.set_override_variables(variables)

    script.execute()
    if script.return_code != 0:
        raise Exception('[ERROR] %s returns %d' %
                        (script_name, script.return_code))

    # Restore title
    if set_console_title and platform.system() == 'Windows':
        ctypes.windll.kernel32.SetConsoleTitleA(saved_title)


def _convert_to_unix_path(path):
    patt = r'^[a-zA-Z]:\\(((?![<>:"/\\|?*]).)+((?<![ .])\\)?)*$'
    if re.match(patt, path):
        path = re.sub(r'^([a-zA-Z]):', lambda x: ('/' +
                                                  x.group(0)[0].lower()), path)
        path = path.replace('\\', '/')
    return path


def get_default_meta():
    return {
        'template': True,
        'hotkey': None,
        'globalHotkey': None,
        'newWindow': False,
        'runAsAdmin': False,
        'autoRun': False,
        'wsl': False,
        'anaconda': False,
        'restartInstance': False,
        'background': False
    }


def load_meta_file(meta_file):
    return yaml.load(open(meta_file, 'r').read(), Loader=yaml.FullLoader)


def save_meta_file(data, meta_file):
    yaml.dump(data, open(meta_file, 'w'), default_flow_style=False)


def get_script_meta(script_path):
    script_meta_file = os.path.splitext(script_path)[0] + '.yaml'
    default_meta_file = os.path.join(
        os.path.dirname(script_path), 'default.yaml')

    meta = get_default_meta()

    data = None
    if os.path.exists(script_meta_file):
        data = load_meta_file(script_meta_file)

    elif os.path.exists(default_meta_file):
        data = load_meta_file(default_meta_file)

    # override default config
    if data is not None:
        for k, v in data.items():
            meta[k] = v

    return meta
