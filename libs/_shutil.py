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
import colorama
import threading
import queue
import locale


def get_conemu_args(title=None, cwd=None, small_window=False):
    CONEMU = r'C:\Program Files\ConEmu\ConEmu64.exe'
    if os.path.exists(CONEMU):
        args = [
            CONEMU,
            '-NoUpdate',
            '-resetdefault',  # '-LoadCfgFile', 'data/ConEmu.xml',
            '-nokeyhooks', '-nomacro', '-nohotkey',
            '-nocloseconfirm',
            # '-GuiMacro', 'palette 1 "<Solarized Light>"',
        ]

        if cwd:
            args += ['-Dir', cwd]
        if title:
            args += ['-Title', title]

        if small_window:
            args += ['-Font', 'Courier', '-Size', '10']
        else:
            args += ['-Max']

        args += [
            '-run',
            '-cur_console:c0'
        ]

        return args
    else:
        return None


def chdir(path, expand=True):
    if expand:
        path = expanduser(path)
    os.chdir(path)


def call(args, cwd=None, env=None, shell=True, highlight=None):
    if highlight is not None:
        return call_highlight(args, shell=shell, cwd=cwd, env=env, highlight=highlight)
    else:
        return subprocess.check_call(args, shell=shell, cwd=cwd, env=env)


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


def replace(file, patt, repl):
    with open(file, 'r') as f:
        s = f.read()

    for x in re.findall(patt, s):
        print('In file "%s":\n  %s => %s' % (file, patt, repl))

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


def call_highlight(args, shell=False, cwd=None, env=None, highlight=None):
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

    def _read_pipe(pipe, que):
        while True:
            data = pipe.readline()
            if data == b'':  # Terminated
                que.put(b'')
                break
            que.put(data)

    assert highlight is not None
    ps = subprocess.Popen(args,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          shell=shell, cwd=cwd, env=env)
    que = queue.Queue()

    threading.Thread(target=_read_pipe, args=(ps.stdout, que)).start()
    threading.Thread(target=_read_pipe, args=(ps.stderr, que)).start()

    terminated = 0
    while True:
        line = que.get()
        if line == b'':
            terminated += 1
            if terminated == 2:
                break

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
