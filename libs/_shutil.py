import subprocess
from subprocess import check_output, Popen
import os
from os import getcwd
from os.path import exists, expanduser, expandvars
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


def write_temp_file(text, ext):
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp:
        temp.write(text.encode('utf-8'))
        return temp.name


def exec_ahk(script):
    assert os.name == 'nt'
    file = write_temp_file(script, '.ahk')
    args = ['AutoHotkeyU64.exe', file]
    Popen(args)
    return args


def conemu_wrap_args(args, title=None, cwd=None, small_window=False):
    CONEMU = r'C:\Program Files\ConEmu\ConEmu64.exe'

    if os.path.exists(CONEMU):
        args2 = [
            CONEMU,
            '-NoUpdate',
            '-resetdefault',  # '-LoadCfgFile', 'data/ConEmu.xml',
            '-nokeyhooks', '-nomacro', '-nohotkey',
            '-nocloseconfirm',
            # '-GuiMacro', 'palette 1 "<Solarized Light>"',
        ]

        if cwd:
            args2 += ['-Dir', cwd]
        if title:
            args2 += ['-Title', title]

        if small_window:
            args2 += ['-Font', 'Courier', '-Size', '10']
        else:
            args2 += ['-Max']

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


def call(args, cwd=None, env=None, shell=True, highlight=None, check_call=True):
    if highlight is not None:
        return call_highlight(args, shell=shell, cwd=cwd, env=env, highlight=highlight)
    else:
        if check_call:
            return subprocess.check_call(args, shell=shell, cwd=cwd, env=env)
        else:
            return subprocess.call(args, shell=shell, cwd=cwd, env=env)


def mkdir(path, expand=True):
    if expand:
        path = expanduser(path)
    os.makedirs(path, exist_ok=True)


def download(url, filename=None):
    try:
        import requests
    except:
        call('pip install requests')
        import requests

    if filename is None:
        filename = os.path.basename(url)

    if exists(filename):
        print('File already exists: %s' % filename)
        return

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
                sys.stdout.write('\r[{}{}]'.format('█' * done, '.' * (50 - done)))
                sys.stdout.flush()
    sys.stdout.write('\n')


def copy(src, dst):
    # Create dirs if not exists
    dir_name = os.path.dirname(dst)
    if not exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)

    if os.path.isdir(src):
        copy_tree(src, dst)

    else:
        file_list = glob.glob(src)
        if len(file_list) == 0:
            raise Exception('No file being found: %s' % src)

        for f in file_list:
            shutil.copy(f, dst)


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
    for f in glob.glob(files):
        os.remove(f)


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


def check_output2(args, shell=None, cwd=None, env=None):
    class MyProcess:
        def __init__(self, ps):
            self.ps = ps

        def _read_pipe(self, pipe, que):
            while True:
                data = pipe.readline()
                if data == b'':  # Terminated
                    que.put(b'')
                    break
                que.put(data)

        def readlines(self):
            import keyboard

            que = queue.Queue()
            threading.Thread(target=self._read_pipe, args=(self.ps.stdout, que)).start()
            threading.Thread(target=self._read_pipe, args=(self.ps.stderr, que)).start()

            terminated = 0
            while True:
                # HACK
                if keyboard.is_pressed('r'):
                    with que.mutex:
                        que.queue.clear()

                line = que.get()
                if line == b'':
                    terminated += 1
                    if terminated == 2:
                        break

                yield line

        def kill(self):
            ps.kill()

        def return_code(self):
            return self.ps.wait()

    ps = subprocess.Popen(args,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          shell=shell, cwd=cwd, env=env)
    return MyProcess(ps)


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

    ps = check_output2(args, shell=shell, cwd=cwd, env=env);
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
    env = os.environ
    env['PATH'] = os.pathsep.join(p) + os.pathsep + env['PATH']


def get_cur_time_str():
    return datetime.datetime.now().strftime('%y%m%d%H%M%S')


env = os.environ
