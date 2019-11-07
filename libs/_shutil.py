import subprocess
from subprocess import check_output, Popen
import os
from os import getcwd
from os.path import exists, expanduser, expandvars, dirname
import sys
import shutil
import platform
from time import sleep
import glob
import re
from distutils.dir_util import copy_tree
import threading
import queue
import locale
import tempfile
from tempfile import gettempdir
import datetime
import signal
import ctypes
import time
import json


def write_temp_file(text, ext):
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp:
        temp.write(text.encode('utf-8'))
        return temp.name


def exec_ahk(script, tmp_script_path=None, wait=True):
    assert os.name == 'nt'
    if not tmp_script_path:
        tmp_script_path = write_temp_file(script, '.ahk')
    else:
        with open(tmp_script_path, 'w') as f:
            f.write(script)
    args = ['AutoHotkeyU64.exe', tmp_script_path]
    if wait:
        return subprocess.call(args)
    else:
        Popen(args)
        return args


def conemu_wrap_args(args, title=None, cwd=None, small_window=False):
    assert sys.platform == 'win32'

    CONEMU = r'C:\Program Files\ConEmu\ConEmu64.exe'

    # Disable update check
    call2(r'reg add HKCU\Software\ConEmu\.Vanilla /v KeyboardHooks /t REG_BINARY /d 02 /f >nul')
    call2(r'reg add HKCU\Software\ConEmu\.Vanilla /v Update.CheckHourly /t REG_BINARY /d 00 /f >nul')
    call2(r'reg add HKCU\Software\ConEmu\.Vanilla /v Update.CheckOnStartup /t REG_BINARY /d 00 /f >nul')

    if os.path.exists(CONEMU):
        args2 = [
            CONEMU,
            '-NoUpdate',
            # '-resetdefault',
            # '-Config', CONF_PATH,
            '-nokeyhooks', '-nomacro', '-nohotkey',
            '-nocloseconfirm',
            # '-GuiMacro', 'palette 1 "<Solarized Light>"',
        ]

        if cwd:
            args2 += ['-Dir', cwd]
        if title:
            args2 += ['-Title', title]

        if small_window:
            args2 += ['-Font', 'Consolas', '-Size', '14']
        else:
            args2 += ['-Max', 'Consolas', '-Size', '14']

        args2 += [
            '-run',
            '-cur_console:c0'
        ]

        return args2 + args
    else:
        raise Exception('ConEmu not installed.')


def chdir(path, expand=True):
    if expand:
        path = expanduser(path)
    os.chdir(path)


def getch(timeout=-1):
    if platform.system() == 'Windows':
        import msvcrt
        import sys
        time_elapsed = 0
        if timeout > 0:
            while not msvcrt.kbhit() and time_elapsed < timeout:
                sleep(0.5)
                time_elapsed += 0.5
                print('.', end='', flush=True)
            return msvcrt.getch().decode(errors='replace') if time_elapsed < timeout else None
        else:
            return msvcrt.getch().decode(errors='replace')

    else:
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


def cd(path, expand=True):
    if expand:
        path = expanduser(path)

    path = os.path.realpath(path)

    if not os.path.exists(path):
        print('"%s" not exist, create? (y/n)' % path)
        if 'y' == getch():
            os.makedirs(path)

    os.chdir(path)


def call2(args):
    subprocess.check_call(args, shell=True)


def call_echo(args):
    print('> ', end='')
    print2(str(args), color='cyan')
    subprocess.check_call(args, shell=True)


def start_in_new_terminal(args, title=None):
    import shlex

    # Convert argument list to string
    if type(args) == list:
        args = [shlex.quote(x) for x in args]

    if platform.system() == 'Windows':
        args = args.replace('|', '^|')  # Escape '|'
        title_arg = ('"' + title + '"') if title else ''
        args = 'start %s cmd /S /C "%s"' % (title_arg, args)
        subprocess.call(args, shell=True)

    elif platform.system() == 'Darwin':
        args = args.replace("'", "'\"'\"'")
        args = args.replace('"', '\\"')
        args = """osascript -e 'tell application "Terminal" to do script "%s"'""" % args
        print(args)
        subprocess.call(args, shell=True)


def call(args, cwd=None, env=None, shell=True, highlight=None, check_call=True):
    if highlight is not None:
        return call_highlight(args, shell=shell, cwd=cwd, env=env, highlight=highlight)
    else:
        if check_call:
            return subprocess.check_call(args, shell=shell, cwd=cwd, env=env)
        else:
            return subprocess.call(args, shell=shell, cwd=cwd, env=env)


def run_in_background(cmd):
    # ANSI escape codes for colors
    GREEN = '\u001b[32;1m'
    YELLOW = '\u001b[33;1m'
    RED = '\u001b[31;1m'
    BLUE = '\u001b[34;1m'
    MAGENTA = '\u001b[35;1m'
    CYAN = '\u001b[36;1m'
    RESET = '\033[0m'

    # Enable ANSI escape sequence processing for the console window by calling
    # the SetConsoleMode Windows API with the ENABLE_VIRTUAL_TERMINAL_PROCESSING
    # flag set.
    if platform.system() == "Windows":
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

    def print_output(ps):
        while True:
            line = ps.stdout.readline()
            # stdout is thread-safe
            sys.stdout.buffer.write(YELLOW.encode() + line + RESET.encode())
            sys.stdout.flush()
            if line == '' and ps.poll() is not None:
                break

    ps = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    t = threading.Thread(target=print_output, args=(ps,))
    t.daemon = True  # Kill the thread when program exits
    t.start()
    return ps


def mkdir(path, expand=True):
    if expand:
        path = expanduser(path)
    os.makedirs(path, exist_ok=True)


def get_pretty_time_delta(seconds):
    sign_string = ' ago' if seconds < 0 else ''
    seconds = abs(int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return '%d day %02d:%02d:%02d%s' % (days, hours, minutes, seconds, sign_string)
    elif hours > 0:
        return '%dh%s' % (hours, sign_string)
    elif minutes > 0:
        return '%d min%s' % (minutes, sign_string)
    else:
        return '%02d sec%s' % (seconds, sign_string)


def download(url, filename=None, redownload=False):
    try:
        import requests
    except:
        subprocess.call([sys.executable, '-m', 'pip', 'install', 'requests'])
        import requests

    if filename is None:
        filename = os.path.basename(url)

    if exists(filename) and not redownload:
        print('File already exists: %s' % filename)
        return filename

    print('Download: %s' % url)
    with open(filename, 'wb') as f:
        response = requests.get(url, stream=True)
        total = response.headers.get('content-length')

        if total is None:
            f.write(response.content)
        else:
            downloaded = 0
            total = int(total)
            for data in response.iter_content(chunk_size=max(int(total / 1000), 1024 * 1024)):
                downloaded += len(data)
                f.write(data)
                done = int(50 * downloaded / total)
                sys.stdout.write('\r[{}{}]'.format(
                    '█' * done, '.' * (50 - done)))
                sys.stdout.flush()
    sys.stdout.write('\n')
    return filename


def copy(src, dst):
    # Create dirs if not exists
    dir_name = os.path.dirname(dst)
    if dir_name and not exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)

    if os.path.isdir(src):
        if dst.endswith('/'):
            dst = os.path.realpath(dst + os.path.basename(src))
            copy_tree(src, dst)
            print('%s => %s' % (src, dst))

    elif os.path.isfile(src):
        shutil.copy(src, dst)
        print('%s => %s' % (src, dst))

    else:
        file_list = glob.glob(src)
        if len(file_list) == 0:
            raise Exception('No file being found: %s' % src)

        for f in file_list:
            copy(f, dst)


def run_elevated(args, wait=True):
    if platform.system() == 'Windows':
        import win32api
        import win32con
        import win32event
        import win32process
        from win32com.shell.shell import ShellExecuteEx
        from win32com.shell import shellcon
        import shlex

        if type(args) == str:
            args = shlex.split(args)

        quoted_args = subprocess.list2cmdline(args[1:])
        process_info = ShellExecuteEx(nShow=win32con.SW_SHOW,
                                      fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
                                      lpVerb='runas',
                                      lpFile=args[0],
                                      lpParameters=quoted_args)
        if wait:
            win32event.WaitForSingleObject(process_info['hProcess'], 600000)
            ret = win32process.GetExitCodeProcess(process_info['hProcess'])
            win32api.CloseHandle(process_info['hProcess'])
        else:
            ret = process_info
    else:
        ret = subprocess.call(['sudo'] + args, shell=True)
    return ret


def remove(files):
    if type(files) == str:
        files = [files]

    for file in files:
        if os.path.isdir(file):
            shutil.rmtree(file)
            print('Delete: %s' % file)
        else:
            for match in glob.glob(file):
                os.remove(match)
                print('Delete: %s' % file)


def replace(file, patt, repl, debug_output=False):
    with open(file, 'r') as f:
        s = f.read()

    if debug_output:
        for x in re.findall(patt, s):
            print('In file "%s":\n  %s => %s' % (file, x, repl))

    s = re.sub(patt, repl, s)

    with open(file, 'w') as f:
        f.write(s)


def append_line(file_path, s):
    lines = None
    with open(file_path, 'r') as f:
        text = f.read()

    if s not in text:
        text += '\n' + s
        with open(file_path, 'w') as f:
            f.write(text)
    else:
        print('[WARNING] Content exists:' + s)


def get_clip():
    import win32clipboard
    win32clipboard.OpenClipboard()
    try:
        text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
    finally:
        win32clipboard.CloseClipboard()
    return text


def set_clip(s):
    try:
        import pyperclip
    except ImportError:
        subprocess.call([sys.executable, '-m', 'pip', 'install', 'pyperclip'])
        import pyperclip

    pyperclip.copy(s)


def check_output2(args, shell=None, cwd=None, env=None):
    class MyProcess:
        def __init__(self, ps):
            self.ps = ps
            self.que = queue.Queue()
            threading.Thread(target=self._read_pipe,
                             args=(self.ps.stdout,)).start()
            threading.Thread(target=self._read_pipe,
                             args=(self.ps.stderr,)).start()

        def _read_pipe(self, pipe):
            while True:
                if ps.poll() is not None:
                    self.que.put(b'')
                    break

                data = pipe.readline()
                if data == b'':  # Terminated
                    self.que.put(b'')
                    break
                self.que.put(data)

        def readlines(self, block=True, timeout=None):
            import keyboard

            terminated = 0
            while True:
                # HACK
                if keyboard.is_pressed('r'):
                    with self.que.mutex:
                        self.que.queue.clear()
                try:
                    line = self.que.get(block=block, timeout=timeout)
                    if line == b'':
                        terminated += 1
                        if terminated == 2:
                            break

                    yield line
                except queue.Empty:
                    yield None

        def readline(self, block=True):
            line = self.que.get(block=block)
            return line

        def kill(self):
            if platform.system() == 'Windows':  # HACK on windows
                subprocess.call(f'taskkill /f /t /pid {self.ps.pid}')
            else:
                self.ps.kill()

        def return_code(self):
            return self.ps.wait()

    ps = subprocess.Popen(args,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          shell=shell, cwd=cwd, env=env)
    return MyProcess(ps)


def check_output_echo(args):
    out = ''
    with subprocess.Popen(args, stdout=subprocess.PIPE, bufsize=1, universal_newlines=True) as p:
        for line in p.stdout:
            print(line, end='')  # process line here
            out += line

    if p.returncode != 0:
        raise subprocess.CalledProcessError(p.returncode, p.args)

    return out


def print2(msg, color='yellow', end='\n'):
    # ANSI escape codes for colors
    COLOR_MAP = {
        'green': '\u001b[32;1m',
        'yellow': '\u001b[33;1m',
        'red': '\u001b[31;1m',
        'blue': '\u001b[34;1m',
        'magenta': '\u001b[35;1m',
        'cyan': '\u001b[36;1m'
    }
    RESET = '\033[0m'

    try:
        print2.initialized
    except AttributeError:
        print2.initialized = False

    # Enable ANSI escape sequence processing for the console window by calling
    # the SetConsoleMode Windows API with the ENABLE_VIRTUAL_TERMINAL_PROCESSING
    # flag set.
    if not print2.initialized and platform.system() == "Windows":
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

    if type(msg) is not str:
        msg = str(msg)
    print(COLOR_MAP[color] + msg + RESET, end=end)


def call_highlight(args, shell=False, cwd=None, env=None, highlight=None, filter_line=None):
    from colorama import init, Fore, Back, Style

    COLOR_MAP = {
        'black': Fore.LIGHTBLACK_EX,
        'red': Fore.LIGHTRED_EX,
        'green': Fore.LIGHTGREEN_EX,
        'yellow': Fore.LIGHTYELLOW_EX,
        'blue': Fore.LIGHTBLUE_EX,
        'magenta': Fore.LIGHTMAGENTA_EX,
        'cyan': Fore.LIGHTCYAN_EX,
        'white': Fore.LIGHTWHITE_EX,
        'BLACK': Back.BLACK,
        'RED': Back.RED,
        'GREEN': Back.GREEN,
        'YELLOW': Back.YELLOW,
        'BLUE': Back.BLUE,
        'MAGENTA': Back.MAGENTA,
        'CYAN': Back.CYAN,
        'WHITE': Back.WHITE,
    }

    init()

    if highlight is None:
        highlight = {}

    ps = check_output2(args, shell=shell, cwd=cwd, env=env)
    for line in ps.readlines():
        # Filter line by pre-defined functions
        if filter_line:
            line = filter_line(line)
            if line is None:
                continue

        index_color_list = []
        for patt, color in highlight.items():
            # Query ANSI character color codes
            if color in COLOR_MAP:
                color = COLOR_MAP[color]

            for match in re.finditer(patt.encode(), line):
                index_color_list.append((match.start(), color.encode()))
                index_color_list.append((match.end(), None))
        index_color_list = sorted(index_color_list, key=lambda x: x[0])

        if len(index_color_list) > 0:
            color_stack = [Style.RESET_ALL.encode()]
            indices, colors = zip(*index_color_list)
            parts = [line[i:j] for i, j in zip(indices, indices[1:] + (None,))]

            line = line[0:indices[0]]
            for i in range(len(parts)):
                if colors[i]:
                    line += colors[i]
                    color_stack.append(colors[i])
                else:
                    color_stack.pop()
                    line += color_stack[-1]
                line += parts[i]

        print(line.decode(locale.getpreferredencoding()), end='')

    ret = ps.return_code()
    if ret != 0:
        raise Exception("Process returned non zero")

    return ret


def prepend_to_path(p):
    if type(p) == list:
        s = os.pathsep.join(p)
    elif type(p) == str:
        s = p
    else:
        raise ValueError()

    os.environ['PATH'] = s + os.pathsep + os.environ['PATH']


def get_cur_time_str():
    return datetime.datetime.now().strftime('%y%m%d%H%M%S')


def exec_bash(script, wsl=False):
    args = None
    if os.name == 'nt':
        if wsl:  # WSL (Windows Subsystem for Linux)
            if not os.path.exists(r'C:\Windows\System32\bash.exe'):
                raise Exception(
                    'WSL (Windows Subsystem for Linux) is not installed.')
            args = ['bash.exe', '-c', script]
        else:
            args = [
                r'C:\Program Files\Git\bin\bash.exe',
                '--login',
                '-i',
                '-c',
                script
            ]
    elif os.name == 'posix':  # MacOSX
        args = ['bash', '-c', script]
    else:
        raise Exception('Non supported OS version')

    # HACK: disable path conversion
    env = os.environ.copy()
    env['MSYS_NO_PATHCONV'] = '1'
    ret = subprocess.call(args, env=env)
    if ret != 0:
        raise Exception('Bash returned non-zero value.')


def get_files(cd=False):
    cur_folder = os.environ['CURRENT_FOLDER']

    if 'SELECTED_FILES' in os.environ:
        files = os.environ['SELECTED_FILES'].split('|')
    else:
        files = list(glob.glob(cur_folder + '/*.*'))

    if cd:
        os.chdir(cur_folder)
        files = [f.replace(cur_folder + os.path.sep, '')
                 for f in files]  # Relative path

    files = [x for x in files if os.path.isfile(x)]
    return files


def cd_current_dir():
    if 'CURRENT_FOLDER' in os.environ:
        os.chdir(os.environ['CURRENT_FOLDER'])
    else:
        os.chdir(os.path.expanduser('~'))


def unzip(file, to=None):
    print('Unzip "%s"...' % file)
    import zipfile
    if to:
        mkdir(to)
    else:
        to = '.'
    with zipfile.ZipFile(file, 'r') as zip:
        zip.extractall(to)


def get_time_str():
    return datetime.datetime.now().strftime('%y%m%d%H%M%S')


def make_and_change_dir(path):
    os.makedirs(path, exist_ok=True)
    os.chdir(path)


def get_pretty_mtime(file):
    dt = os.path.getmtime(file)
    now = time.time()
    seconds = int(dt - now)
    return get_pretty_time_delta(seconds)


def update_env_var_explorer():
    if sys.platform != 'win32':
        return

    try:
        with open(os.path.join(os.environ['TEMP'], 'ExplorerInfo.json')) as f:
            jsn = json.load(f)

        if jsn['currentFolder']:
            os.environ['CURRENT_FOLDER'] = jsn['currentFolder']

        files = jsn['selectedFiles']
        if not files:
            return None

        if len(files) == 1:
            os.environ['SELECTED_FILE'] = files[0]

        if len(files) >= 1:
            os.environ['SELECTED_FILES'] = '|'.join(files)

        return files

    except:
        print('Unable to get explorer info.')
        return None


def try_import(module_name, pkg_name=None):
    import importlib
    if not pkg_name:
        pkg_name = module_name
    try:
        module = importlib.import_module(module_name)
        globals()[module_name] = module
        return module
    except ModuleNotFoundError:
        subprocess.check_call([sys.executable, '-m',
                               'pip', 'install', pkg_name])
        try_import(module_name)


def get_ip_addr():
    if sys.platform == 'win32':
        command = 'powershell -Command "Get-NetIPAddress -AddressFamily IPv4 | foreach { $_.IPAddress }"'
        out = subprocess.check_output(command)
        out = out.decode()
        return out.splitlines()

    return []


def convert_to_unix_path(path):
    patt = r'^[a-zA-Z]:\\(((?![<>:"/\\|?*]).)+((?<![ .])\\)?)*$'
    if re.match(patt, path):
        path = re.sub(r'^([a-zA-Z]):', lambda x: ('/' +
                                                  x.group(0)[0].lower()), path)
        path = path.replace('\\', '/')
    return path


def wait_key(prompt=None, timeout=2):
    if prompt is None:
        prompt = 'Press enter to skip'
    print2(prompt, color='green', end='')
    ch = getch(timeout=timeout)
    print()
    return ch


def start_process(args):
    subprocess.Popen(args, close_fds=True)


env = os.environ
