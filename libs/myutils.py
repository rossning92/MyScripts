import subprocess
import os
import json
import jinja2
import re
import tempfile
import yaml
import platform
import ctypes
import sys

ADD_PARENT_DIRS_TO_PYTHON_PATH = True


def cb_get_file():
    if sys.platform == 'win32':
        import win32clipboard

        file_path = None
        win32clipboard.OpenClipboard(None)

        fmt = 0
        while True:
            fmt = win32clipboard.EnumClipboardFormats(fmt)
            if fmt == 0:
                break

            if fmt > 0xC000:
                fmt_name = win32clipboard.GetClipboardFormatName(fmt)
                # print(fmt_name)

                if fmt_name == 'FileNameW':
                    data = win32clipboard.GetClipboardData(fmt)
                    file_path = data.decode('utf-16').strip('\0x00')

        win32clipboard.CloseClipboard()
        return file_path
    else:
        return None


def open_text_editor(path):
    path = os.path.abspath(os.getcwd() + os.path.sep + path)

    if os.name == 'posix':
        subprocess.Popen(['atom', path])
    else:
        if os.path.splitext(path)[1] == '.py':
            script = ScriptItem('scripts/ext/open_in_PyCharm.py')
            script.execute(path)
            if script.return_code == 0:
                return

        try:
            subprocess.Popen(['notepad++', path])
        except:
            subprocess.Popen(['notepad', path])


def msbuild(vcproj, build_config='Release'):
    print('[ Building `%s`... ]' % os.path.basename(vcproj))

    msbuild = [
        r"C:\Program Files (x86)\Microsoft Visual Studio\2017\Professional\MSBuild\15.0\Bin\MSBuild.exe",
        r"C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\MSBuild\15.0\Bin\MSBuild.exe"
    ]
    msbuild = [x for x in msbuild if os.path.exists(x)]
    assert len(msbuild) > 0

    params = '/p:Configuration=' + build_config + ' /p:WarningLevel=0 /p:Platform=x64 /maxcpucount /verbosity:Quiet /nologo'

    args = '"%s" %s "%s"' % (msbuild[0], params, vcproj)
    ret = subprocess.call(args)
    assert ret == 0


def get_variable_file():
    return os.path.dirname(__file__) + '/../variables.' + platform.node() + '.json'


def get_arg(name):
    with open(get_variable_file(), 'r') as f:
        variables = json.load(f)
    return variables[name][-1]


def append_line(file_path, insert_line):
    lines = None
    with open(file_path, 'r', newline='\n') as f:
        lines = f.readlines()

    if insert_line not in lines:
        lines.append(insert_line)
        with open(file_path, 'w', newline='\n') as f:
            f.writelines(lines)
    else:
        print('[WARNING] Line exists: "%s"' % insert_line)


def bash(cmd):
    if os.name == 'nt':
        return [r'C:\Program Files\Git\bin\bash.exe',
                '--login',
                '-i',
                '-c',
                cmd]
    elif os.name == 'posix':  # MacOSX
        subprocess.call(cmd, shell=True)
    else:
        raise Exception('Non supported OS version')


def write_temp_file(text, ext):
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp:
        temp.write(text.encode('utf-8'))
        return temp.name


def cmd(cmd):
    assert os.name == 'nt'
    file_name = write_temp_file(cmd, '.cmd')
    args = ['cmd.exe', '/c', file_name]
    return args


# TODO: move to a new file
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
        name = name[8:]  # strip starting scripts/
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

        # HACK: Convert to unix path
        if self.ext == '.sh':
            variables = {k: _convert_to_unix_path(v) for k, v in variables.items()}

        if self.override_variables:
            variables = {**variables, **self.override_variables}

        return variables

    def execute(self, args=None, control_down=False):
        if args is None:
            args = []
        elif type(args) == str:
            args = [args]

        env = os.environ.copy()
        cwd = os.path.join(os.getcwd(), os.path.dirname(self.script_path))

        if self.ext == '.ps1':
            if os.name == 'nt':
                script = self.render()
                file_path = write_temp_file(script, '.ps1')
                args = ['PowerShell.exe', '-NoProfile',
                        '-ExecutionPolicy', 'unrestricted',
                        file_path]

        elif self.ext == '.ahk':
            if os.name == 'nt':
                subprocess.Popen(['bin/AutoHotkeyU64.exe', self.script_path])

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
            args = bash(script)

        elif self.ext == '.py':
            script = self.render()
            tmp_script_file = write_temp_file(script, '.py')

            python_path = [os.path.dirname(__file__)]
            if ADD_PARENT_DIRS_TO_PYTHON_PATH:
                script_root_path = os.path.dirname(__file__) + '/../scripts'
                script_root_path = os.path.abspath(script_root_path)
                script_full_path = os.path.join(os.getcwd(), self.script_path)
                parent_dir = os.path.dirname(script_full_path)
                python_path.append(parent_dir)
                while True:
                    parent_dir = os.path.abspath(parent_dir + '/../')
                    if parent_dir.startswith(script_root_path):
                        python_path.append(parent_dir)
                    else:
                        break

            env['PYTHONPATH'] = ';'.join(python_path)
            env['PYTHONDONTWRITEBYTECODE'] = '1'

            if os.name == 'posix':
                args = [sys.executable, tmp_script_file] + args
            else:
                args = [sys.executable, tmp_script_file] + args

            if sys.platform == 'win32' and self.meta['runAsAdmin']:  # HACK: win32 run as admin
                args = ['cmd', '/c',
                        'set', 'PYTHONPATH=' + ';'.join(python_path),
                        'set', 'PYTHONDONTWRITEBYTECODE=1' + ';'.join(python_path),
                        '&'] + args

        else:
            print('Not supported script:', self.ext)

        # Append file if in clipboard
        if args is not None and self.meta['autoRun']:
            file_path = cb_get_file()
            if file_path is not None:
                args.append(file_path)

        # Run commands
        if args is not None and len(args) > 0:

            # Check if new window is needed
            new_window = self.meta['newWindow'] or control_down
            if new_window:
                CONEMU = r'C:\Program Files\ConEmu\ConEmu64.exe'
                if os.path.exists(CONEMU):
                    args = [CONEMU,
                            '-NoUpdate',
                            '-resetdefault',  # '-LoadCfgFile', 'data/ConEmu.xml',
                            '-nokeyhooks', '-nomacro', '-nohotkey',
                            '-nocloseconfirm',
                            '-Dir', cwd,
                            '-Max',
                            '-Title', self.name,
                            '-run',
                            '-cur_console:c0'] + args

                elif os.path.exists(r'C:\Program Files\Git\usr\bin\mintty.exe'):
                    args = [r"C:\Program Files\Git\usr\bin\mintty.exe", '--hold', 'always'] + args

                    # subprocess.Popen(args,
                    #                  creationflags=subprocess.CREATE_NEW_CONSOLE,
                    #                  env=env,
                    #                  cwd=cwd)

            # Check if run as admin
            if self.meta['runAsAdmin']:
                quoted_args = subprocess.list2cmdline(args[1:])
                print(quoted_args)
                ctypes.windll.shell32.ShellExecuteW(
                    None,  # hwnd
                    "runas",  # verb
                    args[0],  # Python executable
                    quoted_args,  # Python file
                    cwd,
                    1)
            else:
                if new_window:
                    subprocess.Popen(args, env=env, cwd=cwd)
                else:
                    self.return_code = subprocess.call(args, env=env, cwd=cwd)

                # if 'autorun' not in self.flags:
                #     # os.utime(self.script_path, None)  # Update modified and access time

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


def find_script(script_name, search_dir='.'):
    script_path = os.path.join(search_dir, script_name)

    if os.path.exists(script_path):
        return script_path

    dir_name = os.path.dirname(script_name)
    if dir_name != '':
        search_dir = dir_name
        script_name = os.path.basename(script_name)

    script_path = None
    for f in os.listdir(search_dir if search_dir else '.'):
        if os.path.isdir(f):
            continue

        if script_name + '.' in f:  # TODO: hack: find script more accurately
            script_path = os.path.join(search_dir, f)

    return script_path


def run_script(script_name, variables=None):
    print('\n>>> RunScript: %s' % script_name)
    script_path = find_script(script_name)
    if script_path is None:
        raise Exception('[ERROR] Cannot find script: "%s"' % script_name)

    script = ScriptItem(script_path)
    script.meta['newWindow'] = False

    if variables:
        script.set_override_variables(variables)

    script.execute()
    if script.return_code != 0:
        raise Exception('[ERROR] %s returns %d' % (script_name, script.return_code))


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
            'newWindow': False,
            'runAsAdmin': False,
            'autoRun': False
        }

        self.meta_file = os.path.splitext(script_path)[0] + '.yaml'
        if os.path.exists(self.meta_file):
            o = yaml.load(open(self.meta_file, 'r').read())
            # override default config
            if o is not None:
                for k, v in o.items():
                    self.meta[k] = v

    def save(self):
        yaml.dump(self.meta, open(self.meta_file, 'w'), default_flow_style=False)


def get_script_meta(script_path):
    return ScriptMeta(script_path).meta
