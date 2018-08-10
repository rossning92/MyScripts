import subprocess
import os
import json
import jinja2
import re
import tempfile


def msbuild(vcproj):
    print('[ Building `%s`... ]' % os.path.basename(vcproj))
    MSBUILD = r'"C:\Program Files (x86)\Microsoft Visual Studio\2017\Professional\MSBuild\15.0\Bin\MSBuild.exe" /p:Configuration=Release /p:WarningLevel=0 /p:Platform=x64 /maxcpucount /verbosity:Quiet /nologo'

    args = '%s "%s"' % (MSBUILD, vcproj)
    ret = subprocess.call(args)
    assert ret == 0


def get_arg(name):
    path = os.path.join(os.path.dirname(__file__), '../variables.json')
    with open(path) as f:
        variables = json.load(f)
    return variables[name]


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
        subprocess.call([
            # r'C:\Program Files\Git\git-bash.exe',
            r'C:\Program Files\Git\bin\bash.exe',
            '--login',
            '-i',
            '-c',
            cmd])
    elif os.name == 'posix':  # MacOSX
        subprocess.call(cmd, shell=True)
    else:
        raise Exception('Non supported OS version')


def cmd(cmd, newterminal=False, runasadmin=False):
    assert os.name == 'nt'
    with tempfile.NamedTemporaryFile(delete=False, suffix='.cmd') as temp:
        # cmd = cmd.replace('\n', '\r\n')  # TODO
        temp.write(cmd.encode('utf-8'))
        temp.flush()

        args = '{}cmd /c {}"{}{}"'.format(
            'bin\Elevate.exe ' if runasadmin else '',
            'start /i cmd /c ' if newterminal else '',
            temp.name,
            ' & if errorlevel 1 pause' if newterminal else ''
        )
        print(args)
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

        self.ext = ext

        patt = r'\[([a-zA-Z_][a-zA-Z_0-9]*)\]'
        self.flags = set(re.findall(patt, name))
        self.name = re.sub(patt, '', name)

    def render(self):
        template = ScriptItem.env.get_template(self.script_path)
        script = template.render({
            'include': ScriptItem.include.__get__(self, ScriptItem),
            **self.get_variables()})
        return script

    def get_variables(self):
        variables = {}
        with open(os.path.dirname(__file__) + '/../variables.json', 'r') as f:
            variables = json.load(f)

        # HACK: Convert to unix path
        if self.ext == '.sh':
            variables = {k: _convert_to_unix_path(v) for k, v in variables.items()}

        return variables

    def execute(self):
        script = self.render()

        # TODO:
        if False:
            assert os.name == 'nt'
            with tempfile.NamedTemporaryFile(delete=False, suffix='.cmd') as temp:
                # cmd = cmd.replace('\n', '\r\n')  # TODO
                temp.write(script.encode('utf-8'))
                temp.flush()

                runasadmin = False
                newterminal = False
                cmdline = '{}cmd /c {}{}{}'.format(
                    'Elevate.exe ' if runasadmin else '',
                    'start /i cmd /c ' if newterminal else '',
                    temp.name,
                    ' & pause' if newterminal or runasadmin else ''
                )
                # params.append('& if errorlevel 1 pause') # Pause when failure

                print(cmdline)
                while not ps.is_terminated():
                    data = ps.read()
                    print(data)
                    if data is not None:
                        print(data.decode(), end='')
                    time.sleep(.1)

                return cmdline

        if self.ext == '.ps1':
            if os.name == 'nt':
                script = self.render()
                subprocess.Popen(
                    ['PowerShell.exe', '-NoProfile',
                     '-ExecutionPolicy', 'unrestricted',
                     '-Command', script])

        elif self.ext == '.ahk':
            if os.name == 'nt':
                subprocess.Popen(['bin/AutoHotkeyU64.exe', self.script_path])

        elif self.ext == '.cmd':
            if os.name == 'nt':
                script = self.render()
                args = cmd(script,
                           runasadmin=('run_as_admin' in self.flags),
                           newterminal=('new_window' in self.flags))
                global __error_code
                __error_code = subprocess.call(args)

                # return args

        elif self.ext == '.sh':
            script = self.render()
            bash(script)

        elif self.ext == '.py':
            script = self.render()

            env = os.environ
            env['PYTHONPATH'] = os.path.dirname(__file__)
            env['PYTHONDONTWRITEBYTECODE'] = '1'

            cwd = os.path.dirname(self.script_path)
            if cwd == '':  # TODO: cwd can not be empty string
                cwd = '.'

            if os.name == 'posix':
                subprocess.call(
                    ['python3', '-c', script], env=env, cwd=cwd)
            else:
                subprocess.call(
                    ['python', '-c', script], env=env, cwd=cwd)

        else:
            print('Not supported script:', self.ext)

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
        assert script_path is not None
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

