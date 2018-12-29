import subprocess
from subprocess import check_output, Popen
import os
from os.path import exists, expanduser, expandvars
import sys
import shutil
import platform
from time import sleep
import glob
import re
from distutils.dir_util import copy_tree


def get_conemu_args(title=None, cwd=None, small_window=False):
    CONEMU = r'C:\Program Files\ConEmu\ConEmu64.exe'
    if os.path.exists(CONEMU):
        args = [
            CONEMU,
            '-NoUpdate',
            '-resetdefault',  # '-LoadCfgFile', 'data/ConEmu.xml',
            '-nokeyhooks', '-nomacro', '-nohotkey',
            '-nocloseconfirm'
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


def call(*kargs, cwd=None, env=None, shell=True):
    return subprocess.call(*kargs, shell=shell, cwd=cwd, env=env)


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
    if dst.endswith('/') or dst.endswith('\\'):
        mkdir(dst)

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
        print('Replace in file "%s": "%s" => "%s"' % (file, patt, repl))

    s = re.sub(patt, repl, s)

    with open(file, 'w') as f:
        f.write(s)


def append_line(file_path, s):
    lines = None
    with open(file_path, 'r') as f:
        text = f.read()

    if s not in text:
        text += '\n' + s
        with open(file_path, 'w', newline='\n') as f:
            f.write(text)
    else:
        print('[WARNING] Content exists:' + s)
