import subprocess
import os
import json
import jinja2
import re
import tempfile
import yaml
import platform
import datetime


def open_text_editor(path):
    if os.name == 'posix':
        subprocess.Popen(['atom', path])
    else:
        subprocess.Popen(['notepad++', path])


def msbuild(vcproj):
    print('[ Building `%s`... ]' % os.path.basename(vcproj))
    MSBUILD = r'"C:\Program Files (x86)\Microsoft Visual Studio\2017\Professional\MSBuild\15.0\Bin\MSBuild.exe" /p:Configuration=Release /p:WarningLevel=0 /p:Platform=x64 /maxcpucount /verbosity:Quiet /nologo'

    args = '%s "%s"' % (MSBUILD, vcproj)
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


def cmd(cmd, runasadmin=False):
    assert os.name == 'nt'
    file_name = write_temp_file(cmd, '.cmd')
    args = ['cmd.exe', '/c', file_name]
    if runasadmin:
        args.insert(0, 'bin\Elevate.exe')
    return args


__error_code = 0


class ScriptItem():
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath="./"))

    def __str__(self):
        return self.name

    def __init__(self, script_path):
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

    def render(self):
        template = ScriptItem.env.get_template(self.script_path)
        ctx = {
            'include': ScriptItem.include.__get__(self, ScriptItem),
            **self.get_variables()
        }
        script = template.render(ctx)
        return script

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

        return variables

    def execute(self):
        args = None
        env = os.environ
        cwd = os.path.dirname(self.script_path)
        if cwd == '':  # TODO: cwd can not be empty string
            cwd = '.'

        if self.ext == '.ps1':
            if os.name == 'nt':
                script = self.render()
                file_path = write_temp_file(script, '.ps1')
                args = ['PowerShell.exe', '-NoProfile',
                        '-ExecutionPolicy', 'unrestricted',
                        file_path]
            if self.meta['runAsAdmin']:
                args.insert(0, 'bin\Elevate.exe')

        elif self.ext == '.ahk':
            if os.name == 'nt':
                subprocess.Popen(['bin/AutoHotkeyU64.exe', self.script_path])

        elif self.ext == '.cmd':
            if os.name == 'nt':
                script = self.render()
                args = cmd(script,
                           runasadmin=self.meta['runAsAdmin'])

        elif self.ext == '.sh':
            script = self.render()
            args = bash(script)

        elif self.ext == '.py':
            script = self.render()

            env['PYTHONPATH'] = os.path.dirname(__file__)
            env['PYTHONDONTWRITEBYTECODE'] = '1'

            if os.name == 'posix':
                args = ['python3', '-c', script]
            else:
                args = ['python', '-c', script]

        else:
            print('Not supported script:', self.ext)

        # Run commands
        if args is not None:
            if self.meta['newWindow']:
                if True:
                    # now = datetime.datetime.now().strftime('%y%m%d_%H%M%S')
                    # args = ['cmd', '/c'] + args + ['|', 'tee', '%Temp%\\Log_' + now + '.txt']
                    subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_CONSOLE, env=env, cwd=cwd)
                else:
                    mintty = [
                        r"C:\Program Files\Git\usr\bin\mintty.exe", '--hold', 'always'
                    ]
                    subprocess.Popen(mintty + args, env=env, cwd=cwd)
            else:
                global __error_code
                __error_code = subprocess.call(args, env=env, cwd=cwd)

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
        script_path = os.path.dirname(self.script_path) + '/' + script_path
        return ScriptItem(script_path).render()


def find_script(script_name, search_dir=None):
    script_path = None
    for f in os.listdir(search_dir if search_dir else '.'):
        if os.path.isdir(f):
            continue

        if script_name + '.' in f:  # TODO: hack: find script more accurately
            script_path = f

    return script_path


def run_script(script_name):
    script_path = find_script(script_name)
    assert script_path is not None

    global __error_code
    __error_code = 0
    script = ScriptItem(script_path)
    script.flags.discard('new_window')
    script.execute()
    assert __error_code == 0


def _convert_to_unix_path(path):
    patt = r'^[a-zA-Z]:\\(((?![<>:"/\\|?*]).)+((?<![ .])\\)?)*$'
    if re.match(patt, path):
        path = re.sub(r'^([a-zA-Z]):', lambda x: ('/' + x.group(0)[0].lower()), path)
        path = path.replace('\\', '/')
    return path


class ScriptMeta():
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
