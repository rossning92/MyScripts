import ctypes
import datetime
import glob
import inspect
import json
import locale
import logging
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unicodedata
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path
from time import sleep
from typing import List, Optional, Union

import yaml

logger = logging.getLogger(__name__)
CONEMU_INSTALL_DIR = r"C:\Program Files\ConEmu"


TITLE_MATCH_MODE_EXACT = 0
TITLE_MATCH_MODE_PARTIAL = 1
TITLE_MATCH_MODE_START_WITH = 2


def control_window_by_name(name, cmd="activate", match_mode=TITLE_MATCH_MODE_EXACT):
    if sys.platform == "win32":
        from ctypes.wintypes import BOOL, HWND, LPARAM

        user32 = ctypes.windll.user32
        matched_hwnd = None

        def callback(hwnd, lParam):
            nonlocal matched_hwnd
            length = user32.GetWindowTextLengthW(hwnd) + 1
            buffer = ctypes.create_unicode_buffer(length)
            user32.GetWindowTextW(hwnd, buffer, length)
            win_text_str = str(buffer.value)
            if match_mode == TITLE_MATCH_MODE_EXACT and name == win_text_str:
                matched_hwnd = hwnd
                return False  # early exit
            elif match_mode == TITLE_MATCH_MODE_PARTIAL and name in win_text_str:
                matched_hwnd = hwnd
                return False  # early exit
            elif match_mode == TITLE_MATCH_MODE_START_WITH and win_text_str.startswith(
                name
            ):
                matched_hwnd = hwnd
                return False  # early exit

            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(BOOL, HWND, LPARAM)
        user32.EnumWindows(WNDENUMPROC(callback), 42)

        if matched_hwnd:
            if cmd == "activate":
                user32.ShowWindow(matched_hwnd, 9)  # in case the window is minimized
                user32.SetForegroundWindow(matched_hwnd)
                return True
            elif cmd == "close":
                WM_CLOSE = 0x10
                ctypes.windll.user32.PostMessageA(matched_hwnd, WM_CLOSE, 0, 0)
            else:
                raise Exception("Invalid cmd parameter: %s" % cmd)

    elif sys.platform == "linux":
        if not shutil.which("xdotool"):
            logging.warning("Skip %s window, xdotool is not installed." % cmd)
            return

        ids = get_output(["xdotool", "search", "--name", name]).split()
        if ids:
            if cmd == "activate":
                subprocess.call(["xdotool", "windowactivate", ids[0]])
                return True
            elif cmd == "close":
                subprocess.call(["xdotool", "windowclose", ids[0]])
                return True
            else:
                raise Exception("Invalid cmd parameter: %s" % cmd)
    return False


def activate_window_by_name(name, match_mode=TITLE_MATCH_MODE_EXACT):
    return control_window_by_name(name=name, cmd="activate", match_mode=match_mode)


def close_window_by_name(name, match_mode=TITLE_MATCH_MODE_EXACT):
    return control_window_by_name(name=name, cmd="close", match_mode=match_mode)


def get_hash(obj, digit=16):
    import hashlib

    if isinstance(obj, str):
        buff = obj.encode("utf-8")
    else:
        buff = repr(obj).encode("utf-8")
    hash_object = hashlib.md5(buff)
    hash = hash_object.hexdigest()[0:digit]
    return hash


_ahk_initialized = False


@lru_cache(maxsize=None)
def get_ahk_exe(uia=True):
    global _ahk_initialized
    if sys.platform != "win32":
        raise Exception("unsupported platform: %s" % sys.platform)

    is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    if not is_admin and uia:
        ahk_exe = os.path.expandvars(r"%ProgramFiles%\AutoHotkey\AutoHotkeyU64_UIA.exe")
    else:
        ahk_exe = os.path.expandvars(r"%ProgramFiles%\AutoHotkey\AutoHotkeyU64.exe")

    if not _ahk_initialized:
        ahk_lib_path = os.path.expandvars(r"%USERPROFILE%\Documents\AutoHotkey\Lib")
        if not os.path.exists(ahk_lib_path):
            os.makedirs(os.path.dirname(ahk_lib_path), exist_ok=True)
            run_elevated(
                r'cmd /c MKLINK /D "{}" "{}"'.format(
                    ahk_lib_path, os.path.abspath(os.path.dirname(__file__) + "/../ahk")
                )
            )
        _ahk_initialized = True

    return ahk_exe


def get_home_path():
    return str(Path.home())


def write_temp_file(text, file_path):
    name, ext = os.path.splitext(file_path)
    if file_path.startswith("."):
        name = ""
        ext = file_path
    else:
        name, ext = os.path.splitext(file_path)

    # Convert into bytes
    if ext in [".bat", ".cmd"]:
        encoding = locale.getpreferredencoding()
    else:
        encoding = "utf-8"
    bytes = text.encode(encoding)
    if ext in [".ahk"]:
        bytes = "\ufeff".encode() + bytes

    if name == "":
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp:
            temp.write(bytes)
            return temp.name
    else:
        full_path = os.path.join(tempfile.gettempdir(), file_path)

        subfolder = os.path.dirname(full_path)
        if subfolder:
            os.makedirs(subfolder, exist_ok=True)

        with open(full_path, "wb") as f:
            f.write(bytes)
            return full_path


def run_ahk(file, wait=False):
    args = [get_ahk_exe(), file]

    with open(os.devnull, "w") as fnull:
        kwargs = {
            "shell": True,  # shell is required for starting UIA process
            "stdin": fnull,
            "stdout": fnull,
            "stderr": fnull,
        }
        if wait:
            subprocess.call(args, **kwargs)
        else:
            return subprocess.Popen(args, **kwargs)


def exec_ahk(script, tmp_script_path=None, wait=True):
    assert sys.platform == "win32"
    if not tmp_script_path:
        tmp_script_path = write_temp_file(script, ".ahk")
    else:
        with open(tmp_script_path, "w", encoding="utf-8") as f:
            f.write("\ufeff")  # BOM utf-8
            f.write(script)
    run_ahk(tmp_script_path, wait=wait)


def wrap_args_conemu(args, title=None, cwd=None, wsl=False, always_on_top=False):
    assert sys.platform == "win32"

    # Disable update check
    PREFIX = r"reg add HKCU\Software\ConEmu\.Vanilla"

    if os.path.exists(CONEMU_INSTALL_DIR):
        call2(PREFIX + " /v KeyboardHooks /t REG_BINARY /d 02 /f >nul")
        call2(PREFIX + " /v Update.CheckHourly /t REG_BINARY /d 00 /f >nul")
        call2(PREFIX + " /v Update.CheckOnStartup /t REG_BINARY /d 00 /f >nul")
        call2(PREFIX + " /v ClipboardConfirmEnter /t REG_BINARY /d 00 /f >nul")
        call2(PREFIX + " /v ClipboardConfirmLonger /t REG_DWORD /d 00 /f >nul")
        call2(PREFIX + " /v Multi.CloseConfirmFlags /t REG_BINARY /d 00 /f >nul")

        args2 = [
            CONEMU_INSTALL_DIR + "\\ConEmu64.exe",
            "-NoUpdate",
            # '-resetdefault',
            # '-Config', CONF_PATH,
            "-nokeyhooks",
            "-nomacro",  # '-nohotkey',
            "-nocloseconfirm",
            "-GuiMacro",
            'palette 1 "<Cobalt2>"',
        ]

        if cwd:
            args2 += ["-Dir", cwd]
        if title:
            args2 += ["-Title", title]

        if always_on_top:
            args2 += [
                "-GuiMacro",
                "WindowPosSize 0 0 80 20",
                "-GuiMacro",
                "SetOption AlwaysOnTop 1",
            ]

        args2 += [
            "-run",
            # Enable exit confirmation
            # "-cur_console:c0",
            # Disable exit confirmation
            "-cur_console:n",
        ]

        # args[0:0] = ['set', 'PATH=%PATH%;C:\Program Files\ConEmu\ConEmu\wsl', '&',
        # CONEMU_INSTALL_DIR + "\\ConEmu\\conemu-cyg-64.exe"]

        return args2 + args
    else:
        raise Exception("ConEmu not installed.")


def chdir(path, expand=True):
    if expand:
        path = os.path.expanduser(path)
    os.chdir(path)


def getch(timeout=-1):
    """Returns None when getch is timeout."""

    if sys.platform == "win32":
        import msvcrt

        time_elapsed = 0.0
        if timeout > 0.0:
            while not msvcrt.kbhit() and time_elapsed < timeout:
                sleep(0.1)
                time_elapsed += 0.1
            if time_elapsed < timeout:
                ch = msvcrt.getch().decode(errors="replace")
            else:
                ch = None
        else:
            ch = msvcrt.getch().decode(errors="replace")

    else:
        import termios
        import tty

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    if ch is not None and ord(ch) == 3:
        raise KeyboardInterrupt
    return ch


def cd(path, expand=True, auto_create_dir=False):
    if expand:
        path = os.path.expanduser(path)
        path = os.path.expandvars(path)

    path = os.path.abspath(path)

    if not os.path.exists(path):
        if auto_create_dir or confirm('"%s" not exist, create?' % path):
            os.makedirs(path)

    os.chdir(path)


def call2(args, check=True, shell=True, **kwargs):
    def quote(s):
        if " " in s:
            s = '"%s"' % s
        return s

    if type(args) == list:
        s = " ".join([quote(x) for x in args])
    else:
        s = args

    logger.debug("shell_cmd: %s" % s)
    subprocess.run(args, check=check, shell=shell, **kwargs)


def call_echo(args, shell=False, check=True, no_output=False, **kwargs):
    def quote(s):
        if " " in s:
            s = '"%s"' % s
        return s

    if type(args) == list:
        s = " ".join([quote(x) for x in args])
    else:
        s = args

    logger.debug("shell_cmd: %s" % s)
    print2("> " + s, color="blue")

    if isinstance(args, str):
        shell = True

    if no_output:
        with fnull() as null:
            ret = subprocess.run(
                args, shell=shell, check=check, stderr=null, stdout=null, **kwargs
            )
    else:
        ret = subprocess.run(args, shell=shell, check=check, **kwargs)
    return ret.returncode


def start_in_new_terminal(args, title=None):
    import shlex

    # Convert argument list to string
    if type(args) == list:
        args = [shlex.quote(x) for x in args]

    if sys.platform == "win32":
        args = args.replace("|", "^|")  # Escape '|'
        title_arg = ('"' + title + '"') if title else ""
        args = 'start %s cmd /S /C "%s"' % (title_arg, args)
        subprocess.call(args, shell=True)

    elif sys.platform == "darwin":
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
    YELLOW = "\u001b[33;1m"
    RESET = "\033[0m"

    # Enable ANSI escape sequence processing for the console window by calling
    # the SetConsoleMode Windows API with the ENABLE_VIRTUAL_TERMINAL_PROCESSING
    # flag set.
    if sys.platform == "win32":
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

    def print_output(ps):
        while True:
            line = ps.stdout.readline()
            # stdout is thread-safe
            sys.stdout.buffer.write(YELLOW.encode() + line + RESET.encode())
            sys.stdout.flush()
            if line == "" and ps.poll() is not None:
                break

    ps = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    t = threading.Thread(target=print_output, args=(ps,))
    t.daemon = True  # Kill the thread when program exits
    t.start()
    return ps


def mkdir(path, expand=True):
    if expand:
        path = os.path.expanduser(path)
    os.makedirs(path, exist_ok=True)


def get_pretty_time_delta(seconds):
    sign_string = " ago" if seconds < 0 else ""
    seconds = abs(int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return "%d day %02d:%02d:%02d%s" % (days, hours, minutes, seconds, sign_string)
    elif hours > 0:
        return "%dh%s" % (hours, sign_string)
    elif minutes > 0:
        return "%d min%s" % (minutes, sign_string)
    else:
        return "%02d sec%s" % (seconds, sign_string)


def download(url, filename=None, redownload=False, save_to_tmp=False):
    try:
        import requests
    except:
        subprocess.call([sys.executable, "-m", "pip", "install", "requests"])
        import requests

    if filename is None:
        filename = os.path.basename(url)
        if save_to_tmp:
            filename = os.path.join(tempfile.gettempdir(), filename)

    if os.path.exists(filename) and not redownload:
        print("File already exists: %s" % filename)
        return filename

    print("Download: %s" % url)
    with open(filename, "wb") as f:
        response = requests.get(url, stream=True)
        total = response.headers.get("content-length")

        if total is None:
            f.write(response.content)
        else:
            downloaded = 0
            total = int(total)
            for data in response.iter_content(
                chunk_size=max(int(total / 1000), 1024 * 1024)
            ):
                downloaded += len(data)
                f.write(data)
                done = int(50 * downloaded / total)
                sys.stdout.write("\r[{}{}]".format("|" * done, "." * (50 - done)))
                sys.stdout.flush()
    sys.stdout.write("\n")
    return filename


def copy(src, dst, overwrite=False):
    # Lazy import: distutils import is pretty slow
    from distutils.dir_util import copy_tree

    # Create dirs if not exists
    dir_name = os.path.dirname(dst)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)

    if os.path.isdir(src):
        if dst.endswith("/"):
            dst = os.path.abspath(dst + os.path.basename(src))
            copy_tree(src, dst)
            print("%s => %s" % (src, dst))
        else:
            copy_tree(src, dst)
            print("%s => %s" % (src, dst))

    elif os.path.isfile(src):
        if overwrite or not os.path.exists(dst):
            shutil.copy2(src, dst)
            print("%s => %s" % (src, dst))

    else:
        file_list = glob.glob(src)
        if len(file_list) == 0:
            raise Exception("No file being found: %s" % src)

        for f in file_list:
            copy(f, dst)


def run_elevated(args: Union[List, str], wait=True, show_terminal_window=True):
    if sys.platform == "win32":
        import win32con
        from win32com.shell import shellcon
        from win32com.shell.shell import ShellExecuteEx

        if type(args) == str:
            lpFile, lpParameters = args.split(" ", 1)
        else:
            lpFile = args[0]
            lpParameters = subprocess.list2cmdline(args[1:])

        process_info = ShellExecuteEx(
            nShow=win32con.SW_SHOW if show_terminal_window else win32con.SW_HIDE,
            fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
            lpVerb="runas",
            lpFile=lpFile,
            lpParameters=lpParameters,
        )
        if wait:
            h = process_info["hProcess"].handle
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            if kernel32.WaitForSingleObject(h, 600000) == 0:  # WAIT_OBJECT_0
                exit_code = ctypes.c_ulong()
                if kernel32.GetExitCodeProcess(h, ctypes.byref(exit_code)):
                    ret = exit_code.value
                else:
                    raise ctypes.WinError(ctypes.get_last_error())
            else:
                raise Exception("WaitForSingleObject failed")

            kernel32.CloseHandle(h)
        else:
            ret = process_info
    else:
        if type(args) == str:
            args = "sudo " + args
        else:
            args = ["sudo"] + args
        logging.info("run_elevated(): %s" % args)
        ret = subprocess.call(args, shell=True)
    return ret


def remove(files):
    if type(files) == str:
        files = [files]

    for file in files:
        if os.path.isdir(file):
            shutil.rmtree(file)
            print("Deleted: %s" % file)
        else:
            for match in glob.glob(file):
                os.remove(match)
                print("Deleted: %s" % match)


def rename(src, dst, dry_run=False):
    if src == dst:
        print('Skip: "%s" and "%s" are the same file' % (src, dst))
        return

    print("Rename: %s => %s" % (src, dst))
    if not dry_run:
        os.rename(src, dst)


def get_clip():
    import win32clipboard

    win32clipboard.OpenClipboard()
    try:
        text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
    finally:
        win32clipboard.CloseClipboard()
    return text


@lru_cache(maxsize=None)
def is_in_termux():
    return shutil.which("termux-setup-storage") is not None


def set_clip(s):
    if is_in_termux():
        if not shutil.which("termux-clipboard-set"):
            subprocess.check_call(["pkg", "install", "termux-api"])
        subprocess.check_call(["termux-clipboard-set", s])
    else:
        try:
            import pyperclip
        except ImportError:
            subprocess.call([sys.executable, "-m", "pip", "install", "pyperclip"])
            import pyperclip

        pyperclip.copy(s)


def fnull():
    return open(os.devnull, "w")


def read_lines(file):
    with open(file) as f:
        return f.read().splitlines()


def write_lines(file, lines):
    with open(file, newline="\n") as f:
        f.write("\n".join(lines))


def read_proc_lines(
    args, echo=False, read_err=False, max_lines=None, check=True, **kwargs
):
    ps = subprocess.Popen(
        args,
        stdout=subprocess.PIPE if (not read_err) else None,
        stderr=subprocess.PIPE if read_err else None,
        # bufsize=1,
        **kwargs,
    )

    def terminate():
        nonlocal ps
        if sys.platform == "win32":
            FNULL = open(os.devnull, "w")
            subprocess.call(
                ["taskkill", "/f", "/t", "/pid", "%d" % ps.pid],
                stdout=FNULL,
                stderr=FNULL,
            )
        else:
            ps.send_signal(signal.SIGINT)
            ps.kill()

    line_no = 0
    for line in ps.stderr if read_err else ps.stdout:
        try:
            # process line here
            line = line.strip()
            line = line.decode(errors="ignore")
            if echo:
                print(line)

            yield line
            line_no += 1

            if max_lines and line_no >= max_lines:
                terminate()
                break

        except GeneratorExit:
            terminate()
            raise

    ps.wait()
    if check and ps.returncode != 0:
        raise subprocess.CalledProcessError(ps.returncode, ps.args)


def check_output_echo(args):
    out = ""
    with subprocess.Popen(
        args, stdout=subprocess.PIPE, bufsize=1, universal_newlines=True
    ) as p:
        for line in p.stdout:
            print(line, end="")  # process line here
            out += line

    if p.returncode != 0:
        raise subprocess.CalledProcessError(p.returncode, p.args)

    return out


def get_output(args, **kwargs):
    return (
        subprocess.Popen(
            args, universal_newlines=True, stdout=subprocess.PIPE, **kwargs
        )
        .stdout.read()
        .strip()
    )


def supports_color():
    """
    Returns True if the running system's terminal supports color, and False
    otherwise.
    """
    plat = sys.platform
    supported_platform = plat != "Pocket PC" and (
        plat != "win32" or "ANSICON" in os.environ
    )
    # isatty is not always implemented, #6223.
    is_a_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
    return supported_platform and is_a_tty


_console_color_initialized = False


def print2(msg, color="yellow", end="\n"):
    # https://gist.github.com/dominikwilkowski/60eed2ea722183769d586c76f22098dd
    # ANSI escape codes for colors
    COLOR_MAP = {
        "black": "\u001b[30;1m",
        "blue": "\u001b[34;1m",
        "cyan": "\u001b[36;1m",
        "green": "\u001b[32;1m",
        "magenta": "\u001b[35;1m",
        "red": "\u001b[31;1m",
        "RED": "\u001b[41;1m",
        "white": "\u001b[37;1m",
        "yellow": "\u001b[33;1m",
        "YELLOW": "\u001b[43;1m",
    }
    RESET = "\033[0m"

    # Enable ANSI escape sequence processing for the console window by calling
    # the SetConsoleMode Windows API with the ENABLE_VIRTUAL_TERMINAL_PROCESSING
    # flag set.
    global _console_color_initialized
    if not _console_color_initialized:
        if sys.platform == "win32":
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        _console_color_initialized = True

    if type(msg) is not str:
        msg = str(msg)
    print(COLOR_MAP[color] + msg + RESET, end=end, flush=True)


def call_highlight(args, highlight=None, filter_line=None, **kwargs):
    from colorama import Back, Fore, Style, init

    COLOR_MAP = {
        "black": Fore.LIGHTBLACK_EX,
        "red": Fore.LIGHTRED_EX,
        "green": Fore.LIGHTGREEN_EX,
        "yellow": Fore.LIGHTYELLOW_EX,
        "blue": Fore.LIGHTBLUE_EX,
        "magenta": Fore.LIGHTMAGENTA_EX,
        "cyan": Fore.LIGHTCYAN_EX,
        "white": Fore.LIGHTWHITE_EX,
        "BLACK": Back.BLACK,
        "RED": Back.RED,
        "GREEN": Back.GREEN,
        "YELLOW": Back.YELLOW,
        "BLUE": Back.BLUE,
        "MAGENTA": Back.MAGENTA,
        "CYAN": Back.CYAN,
        "WHITE": Back.WHITE,
    }

    init()

    if highlight is None:
        highlight = {}

    for line in read_proc_lines(args, **kwargs):
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

            for match in re.finditer(patt, line):
                index_color_list.append((match.start(), color))
                index_color_list.append((match.end(), None))
        index_color_list = sorted(index_color_list, key=lambda x: x[0])

        if len(index_color_list) > 0:
            color_stack = [Style.RESET_ALL]
            indices, colors = zip(*index_color_list)
            parts = [line[i:j] for i, j in zip(indices, indices[1:] + (None,))]

            line = line[0 : indices[0]]
            for i in range(len(parts)):
                if colors[i]:
                    line += colors[i]
                    color_stack.append(colors[i])
                else:
                    color_stack.pop()
                    line += color_stack[-1]
                line += parts[i]

        print(line)


def get_short_path_name(long_name):
    assert sys.platform == "win32"

    import ctypes
    from ctypes import wintypes

    _GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
    _GetShortPathNameW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.LPWSTR,
        wintypes.DWORD,
    ]
    _GetShortPathNameW.restype = wintypes.DWORD

    output_buf_size = 0
    while True:
        output_buf = ctypes.create_unicode_buffer(output_buf_size)
        needed = _GetShortPathNameW(long_name, output_buf, output_buf_size)
        if output_buf_size >= needed:
            return output_buf.value
        else:
            output_buf_size = needed


def prepend_to_path(paths, env=None):
    if env is None:
        env = os.environ

    if type(paths) == list:
        pass
    elif type(paths) == str:
        paths = paths.split(os.pathsep)
    else:
        raise ValueError()
    logging.debug("prepend_to_path(): %s" % os.pathsep.join(paths))

    if "PATH" in env:
        paths += env["PATH"].split(os.pathsep)
    else:
        paths += os.environ["PATH"].split(os.pathsep)

    # Remove non-existing directories
    paths = [p for p in paths if os.path.exists(p)]
    s = os.pathsep.join(paths)

    # Update PATH environmental variable
    env["PATH"] = s


def get_cur_time_str():
    return datetime.datetime.now().strftime("%y%m%d%H%M%S")


def get_date_str():
    return datetime.datetime.now().strftime("%Y%m%d")


def exec_bash(script, wsl=False, echo=False):
    logging.debug("exec_bash: bash commands: %s" % script)
    args = None
    if sys.platform == "win32":
        if wsl:  # WSL (Windows Subsystem for Linux)
            if not os.path.exists(r"C:\Windows\System32\bash.exe"):
                raise Exception("WSL (Windows Subsystem for Linux) is not installed.")
            args = ["bash.exe", "-c", script]
        else:
            if echo:
                print("> ", end="")
                print2(str(script), color="cyan")
            args = [r"C:\Program Files\Git\bin\bash.exe", "--login", "-i", "-c", script]
    elif os.name == "posix":  # MacOSX
        args = ["bash", "-c", script]
    else:
        raise Exception("Non supported OS version")

    # HACK: disable path conversion
    env = os.environ.copy()
    env["MSYS_NO_PATHCONV"] = "1"
    ret = subprocess.call(args, env=env)
    if ret != 0:
        raise Exception("Bash returned non-zero value.")


def get_files(cd=False, ignore_dirs=True):
    files = []
    if "FILES" in os.environ:
        files = os.environ["FILES"].split("|")
        files = sorted(files)

    if "CWD" in os.environ and cd:
        cur_folder = os.environ["CWD"]
        os.chdir(cur_folder)
        files = [f.replace(cur_folder, "") for f in files]  # Relative path
        files = [x.lstrip(os.path.sep) for x in files]

    if ignore_dirs:
        files = [x for x in files if os.path.isfile(x)]
    return files


def get_selected_folder():
    files = os.environ["FILES"].split("|")
    folders = [x for x in files if os.path.isdir(x)]
    return folders[0]


def get_current_folder():
    if "CWD" not in os.environ:
        d = input("Enter directory path: ")
        if not d:
            raise Exception("directory cannot be empty.")
        return d
    else:
        return os.environ["CWD"]


def cd_current_dir():
    if "CWD" in os.environ:
        os.chdir(os.environ["CWD"])
    else:
        os.chdir(os.path.expanduser("~"))


def zip_file(path, out_file):
    shutil.make_archive(out_file.rstrip(".zip"), "zip", path)


def unzip(file, to=None):
    print('Unzip "%s"...' % file)
    import zipfile

    if to:
        os.makedirs(to, exist_ok=True)
    else:
        to = "."
    with zipfile.ZipFile(file, "r") as zip:
        zip.extractall(to)


def get_time_str():
    return datetime.datetime.now().strftime("%y%m%d_%H%M%S")


def get_date_str():
    return datetime.datetime.now().strftime("%y%m%d")


def make_and_change_dir(path):
    os.makedirs(path, exist_ok=True)
    os.chdir(path)


def get_pretty_mtime(file):
    dt = os.path.getmtime(file)
    now = time.time()
    seconds = int(dt - now)
    return get_pretty_time_delta(seconds)


def clear_env_var_explorer():
    os.environ.pop("CWD", None)
    os.environ.pop("FILE", None)
    os.environ.pop("FILES", None)


def update_env_var_explorer():
    if sys.platform == "win32":
        try:
            with open(os.path.join(os.environ["TEMP"], "ow_explorer_info.json")) as f:
                data = json.load(f)

            if data["current_folder"]:
                os.environ["CWD"] = data["current_folder"]
            elif "CWD" in os.environ:
                del os.environ["CWD"]

            files = data["selected_files"]
            if len(files) >= 1:
                os.environ["FILE"] = files[0]
                os.environ["FILES"] = "|".join(files)
            else:
                if "FILE" in os.environ:
                    del os.environ["FILE"]
                if "FILES" in os.environ:
                    del os.environ["FILES"]
            return files

        except Exception:
            print("Unable to get explorer info.")


def try_import(module_name, pkg_name=None):
    import importlib

    if not pkg_name:
        pkg_name = module_name
    try:
        module = importlib.import_module(module_name)
        globals()[module_name] = module
        return module
    except ModuleNotFoundError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_name])
        try_import(module_name)


def get_ip_addresses():
    return [
        info[4][0]
        for info in socket.getaddrinfo(socket.gethostname(), None)
        if info[0] == socket.AddressFamily.AF_INET
    ]


def check_output(args, **kwargs):
    return subprocess.check_output(args, universal_newlines=True, **kwargs)


def convert_to_unix_path(path, wsl=False):
    path = path.replace("\\", "/")
    PATT = r'^[a-zA-Z]:/(((?![<>:"//|?*]).)+((?<![ .])/)?)*$'
    if re.match(PATT, path):
        if wsl:
            path = re.sub(
                r"^([a-zA-Z]):", lambda x: ("/mnt/" + x.group(0)[0].lower()), path
            )
        else:
            path = re.sub(
                r"^([a-zA-Z]):", lambda x: ("/" + x.group(0)[0].lower()), path
            )
    return path


def append_to_path_global(path):
    if sys.platform == "win32":
        if False and " " in path:
            path = get_short_path_name(path)

        s = get_output(r"reg query HKCU\Environment /v PATH")
        s = re.search(r"PATH\s+(?:REG_SZ|REG_EXPAND_SZ)\s+(.*)", s).group(1).strip()
        paths = s.split(";")
        new_paths = []
        for p in paths:
            if os.path.isdir(p):
                new_paths.append(p)
            else:
                logging.debug("Removed from PATH: %s" % p)

        if path not in new_paths:
            new_paths.append(path)
            logging.debug("Added to PATH: %s" % path)

        with fnull() as nul:
            subprocess.call(["setx", "PATH", ";".join(new_paths)], stdout=nul)


def wait_key(prompt=None, timeout=5):
    if prompt is None:
        prompt = "Press enter to skip"
    print2(prompt, color="green", end="")
    ch = getch(timeout=timeout)
    print()
    return ch


def wait_for_key(keys):
    from functools import partial

    import keyboard

    if type(keys) is str:
        keys = [keys]

    lock = threading.Event()
    handlers = []

    pressed = None

    def key_pressed(key):
        nonlocal pressed
        pressed = key
        lock.set()

    for key in keys:
        handler = keyboard.add_hotkey(key, partial(key_pressed, key), suppress=True)
        handlers.append(handler)

    lock.wait()

    for handler in handlers:
        keyboard.remove_hotkey(handler)

    return pressed


def wait_until_file_modified(f):
    last_mtime = os.path.getmtime(f)
    while True:
        time.sleep(0.2)
        mtime = os.path.getmtime(f)
        if mtime > last_mtime:
            return


def shell_execute(args):
    from ctypes import c_char_p, c_int, c_ulong, c_void_p
    from ctypes.wintypes import BOOL, DWORD, HANDLE, HINSTANCE, HKEY, HWND

    class ShellExecuteInfo(ctypes.Structure):
        _fields_ = [
            ("cbSize", DWORD),
            ("fMask", c_ulong),
            ("hwnd", HWND),
            ("lpVerb", c_char_p),
            ("lpFile", c_char_p),
            ("lpParameters", c_char_p),
            ("lpDirectory", c_char_p),
            ("nShow", c_int),
            ("hInstApp", HINSTANCE),
            ("lpIDList", c_void_p),
            ("lpClass", c_char_p),
            ("hKeyClass", HKEY),
            ("dwHotKey", DWORD),
            ("hIcon", HANDLE),
            ("hProcess", HANDLE),
        ]

        def __init__(self, **kw):
            ctypes.Structure.__init__(self)
            self.cbSize = ctypes.sizeof(self)
            for field_name, field_value in kw.items():
                setattr(self, field_name, field_value)

    PShellExecuteInfo = ctypes.POINTER(ShellExecuteInfo)

    ShellExecuteEx = ctypes.windll.Shell32.ShellExecuteExA
    ShellExecuteEx.argtypes = (PShellExecuteInfo,)
    ShellExecuteEx.restype = BOOL

    SW_SHOW = 5

    params = args[1:]
    input(params)

    execute_info = ShellExecuteInfo(
        fMask=0,
        hwnd=None,
        lpFile=args[0].encode("utf-8"),
        lpParameters=subprocess.list2cmdline(params).encode("utf-8"),
        lpDirectory=None,
        nShow=SW_SHOW,
    )

    if not all(stream.isatty() for stream in (sys.stdin, sys.stdout, sys.stderr)):
        # TODO: Some streams were redirected, we need to manually work them
        raise NotImplementedError("Redirection is not supported")

    if not ShellExecuteEx(ctypes.byref(execute_info)):
        raise ctypes.WinError()


def start_process(args, shell=False):
    creationflags = 0
    if sys.platform == "win32":
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        DETACHED_PROCESS = 0x00000008
        creationflags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP

    start_new_session = False
    if sys.platform == "linux":
        start_new_session = True

    with open(os.devnull) as nul:
        subprocess.Popen(
            args,
            shell=shell,
            creationflags=creationflags,
            start_new_session=start_new_session,
            stderr=nul,
            stdout=nul,
        )


def setup_nodejs(install=True):
    if sys.platform == "win32":
        NODE_JS_PATH = r"C:\Program Files\nodejs"
        if install and not os.path.exists(NODE_JS_PATH):
            run_elevated("choco install nodejs -y")

        if os.path.exists(NODE_JS_PATH):
            logging.info("Node.js: install path: %s" % NODE_JS_PATH)

            prepend_to_path(
                [
                    NODE_JS_PATH,
                    os.path.expandvars("%APPDATA%\\npm"),
                    os.path.expandvars("%USERPROFILE%\\node_modules\\.bin"),
                    os.path.expandvars("%LOCALAPPDATA%\\Yarn\\bin"),
                    os.path.expandvars("%ProgramFiles%\\Yarn\\bin\\yarn.cmd"),
                    os.path.expandvars("%ProgramFiles(x86)%\\Yarn\\bin\\yarn.cmd"),
                ]
            )

        node_path = [os.path.abspath(os.path.dirname(__file__) + "/../jslib")]

        npm_modules = os.path.expandvars(r"%APPDATA%\npm\node_modules")
        if os.path.exists(npm_modules):
            node_path.append(npm_modules)

        yarn_modules = os.path.expandvars(
            r"%LOCALAPPDATA%\Yarn\Data\global\node_modules"
        )
        if os.path.exists(yarn_modules):
            node_path.append(yarn_modules)

        node_path = os.path.pathsep.join(node_path)
        os.environ["NODE_PATH"] = node_path
        logging.info("Node.js: NODE_PATH: %s" % node_path)

    else:
        logging.warning("Node.js: not supported for current OS.")


def npm_install(cwd="."):
    cwd = os.path.abspath(cwd)
    if not os.path.exists(os.path.join(cwd, "node_modules")):
        call_echo("yarn", cwd=cwd)


def get_next_file_name(file):
    POSTFIX_START = "-02"

    name, ext = os.path.splitext(file)
    basename = os.path.basename(name)
    folder = os.path.dirname(name)
    match = re.search("^(.*?)(\d*)$", basename)

    if match is not None and match.group(2):
        prefix = match.group(1)
        digits = match.group(2)
        len_digits = len(digits)
        digits = int(digits)
        new_digits = ("{:0%dd}" % len_digits).format(digits + 1)
        if len(new_digits) == len_digits:
            new_file = os.path.join(folder, prefix + new_digits + ext)
        else:
            new_file = name + POSTFIX_START + ext
    else:
        new_file = name + POSTFIX_START + ext

    if os.path.exists(new_file):
        new_file = name + POSTFIX_START + ext

    return new_file


def confirm(msg=""):
    msg += " (y/n): "
    print2(msg, end="", color="green")
    ch = getch()
    print()
    return ch == "y"


def shell_open(file="."):
    if sys.platform == "win32":
        file = file.replace("/", os.path.sep)
        os.startfile(file)

    elif sys.platform == "darwin":
        subprocess.Popen(["open", file])

    else:
        try:
            start_process(["xdg-open", file])
        except OSError:
            # er, think of something else to try
            # xdg-open *should* be supported by recent Gnome, KDE, Xfce
            pass


def write_text_file(content, file, overwrite=True):
    content = content.strip()

    # Don't rewrite the file if content does not change.
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            s = f.read()

        if s == content:
            return False

    if not os.path.exists(file) or overwrite:
        with open(file, "w", encoding="utf-8") as f:
            f.write(content.strip())

    return True


def refresh_env_vars():
    if sys.platform == "win32":
        REG_KEYS = [
            r"HKLM\System\CurrentControlSet\Control\Session Manager\Environment",
            r"HKCU\Environment",
        ]

        def strip_path(p):
            return p.strip().rstrip(os.path.sep)

        paths = [strip_path(x) for x in os.environ["PATH"].split(os.pathsep)]

        for reg_path in REG_KEYS:
            out = subprocess.check_output(
                ["reg", "query", reg_path], universal_newlines=True
            )
            lines = out.splitlines()
            lines = [x.strip() for x in lines if x.strip()]
            lines = lines[1:]  # skip the first line

            for line in lines:
                cols = line.split(maxsplit=2)
                if cols[0].upper() == "PATH":
                    new_paths = cols[2]
                    new_paths = new_paths.split(os.pathsep)

                    for p in new_paths:
                        p = strip_path(p)

                        # Add to PATH if not exists
                        if p and p not in paths:
                            logging.debug("Add to PATH: %s" % p)
                            paths.append(p)

        os.environ["PATH"] = os.pathsep.join(paths)


def get_newest_file(wildcard):
    max_mtime = 0.0
    newest_file = None
    for f in glob.glob(wildcard):
        mtime = os.path.getmtime(f)
        if mtime > max_mtime:
            newest_file = f
            max_mtime = mtime
    return newest_file


def wait_for_new_file(file_pattern, allow_exists=False):
    max_mtime = 0.0
    newest_file = None
    for f in glob.glob(file_pattern):
        mtime = os.path.getmtime(f)
        if mtime > max_mtime:
            newest_file = f
            max_mtime = mtime

    if allow_exists:
        return newest_file
    else:
        print("wait for new file: %s " % file_pattern)
        while True:
            for f in glob.glob(file_pattern, recursive=True):
                mtime = os.path.getmtime(f)
                if mtime > max_mtime:
                    # Wait until file is closed
                    try:
                        os.rename(newest_file, newest_file)
                        print("file created: %s" % newest_file)
                        return newest_file
                    except:
                        time.sleep(0.1)


def slugify(value, allow_unicode=True):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")


def get_script_root():
    return os.path.abspath(os.path.dirname(__file__) + "/../scripts")


def load_json(file, default=None):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        if default is not None:
            return default
        else:
            raise Exception("Default value is not specified.")


def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def update_json(file, dict_):
    dir = os.path.dirname(file)
    if dir:
        os.makedirs(dir, exist_ok=True)
    data = load_json(file, default={})
    data.update(dict_)
    save_json(file, data)


def screen_record(out_file, rect=None, mouse_cursor=True):
    args = [
        "ffmpeg",
        "-y",
        "-f",
        "gdigrab",
        "-draw_mouse",
        "%d" % int(mouse_cursor),
        "-framerate",
        "60",
    ]
    if rect is not None:
        args += [
            "-offset_x",
            "%d" % rect[0],
            "-offset_y",
            "%d" % rect[1],
            "-video_size",
            "%dx%d" % (rect[2], rect[3]),
        ]
    args += [
        "-i",
        "desktop",
        "-c:v",
        "libx264",
        "-crf",
        "0",
        "-preset",
        "ultrafast",
        out_file,
    ]
    ps = subprocess.Popen(args, stdin=subprocess.PIPE)

    def stop():
        ps.stdin.write(b"q")
        ps.stdin.close()

    return stop


def kill_proc(ps):
    if sys.platform == "win32":
        subprocess.call("TASKKILL /F /T /PID %d >NUL 2>NUL" % ps.pid, shell=True)


def send_ctrl_c(ps):
    if ps.poll() is None:
        if sys.platform == "win32":
            try:
                ctypes.windll.kernel32.GenerateConsoleCtrlEvent(0, 0)
                ps.wait()
            except KeyboardInterrupt:
                # It sends ctrl-c to all processes that share the console of the calling
                # process but then ignores it in the python process with an exception
                # handler.
                pass
        else:
            ps.send_signal(signal.CTRL_C_EVENT)
            ps.wait()


def get_temp_file_name(suffix=None):
    with tempfile.TemporaryFile(suffix=suffix) as f:
        return f.name


def find_newest_file(wildcard) -> Optional[str]:
    files = list(glob.glob(wildcard, recursive=True))
    files.sort(key=os.path.getmtime)
    if len(files) > 0:
        return files[-1]
    else:
        return None


def move_file(src, dst, overwrite=False):
    dst = os.path.abspath(dst)
    assert os.path.exists(src)
    os.makedirs(os.path.dirname(dst), exist_ok=True)

    if overwrite and os.path.exists(dst):
        os.remove(dst)

    shutil.move(src, dst)


class MenuItem:
    def __init__(self, name, key, func, caller) -> None:
        self.name = name
        self.caller = caller
        self.key = key
        self.func = func

    def __str__(self) -> str:
        s = ""
        if self.key:
            s += "[%s] " % self.key.replace("\t", "tab").replace("\r", "enter")
        s += self.name
        return s


_menu_items: List[MenuItem] = []


def menu_item(*, key=None, name=None):
    def decorator(func):
        nonlocal name
        if name is None:
            name = func.__name__

        caller = inspect.stack()[1].filename
        _menu_items.append(MenuItem(name=name, key=key, func=func, caller=caller))

        return func

    return decorator


def menu_loop(
    run_periotic=None,
    interval=-1,
    sort_by_name=True,
    unique_key=False,
    all_modules=False,
):
    if all_modules:
        menu_items = _menu_items
    else:
        caller = inspect.stack()[1].filename
        menu_items = list(filter(lambda x: x.caller == caller, _menu_items))

    if sort_by_name:
        menu_items = sorted(menu_items, key=lambda x: x.name)

    if unique_key:
        used_keys = set()
        for item in menu_items:
            if item.key in used_keys:
                raise Exception("Key conflict: %s" % item.key)
            used_keys.add(item.key)

    def print_help():
        print()
        print2("Help Menu")
        print2("---------")

        for menu_item in menu_items:
            print(f"  {menu_item}")

        print("  [h] help")
        print("  [q] quit")
        print()

    def func_wrapper(func):
        start_time = time.time()
        try:
            func()
        except Exception as ex:
            print2("Error: %s" % ex, color="red")
        end_time = time.time()
        if end_time - start_time > 1:
            print2(
                "(finished in %.2f secs)" % (end_time - start_time),
                color="blue",
            )

    print_help()
    while True:
        try:
            if run_periotic is not None and interval > 0:
                while True:
                    ch = getch(timeout=interval)
                    if ch != None:
                        break
                    else:
                        run_periotic()
            else:
                ch = getch()
        except KeyboardInterrupt:
            sys.exit(0)

        if ch == "h":
            print_help()
        elif ch == "q":
            break
        elif ch == "\t":
            from _term import select_option

            index = select_option(menu_items)
            if index >= 0:
                func_wrapper(menu_items[index].func)

        else:
            match = list(filter(lambda x: x.key == ch, menu_items))
            if len(match) == 0:
                print2("Invalid key: %s" % ch, color="yellow")
            else:
                if len(match) == 1:
                    match = match[0]
                else:
                    for i, item in enumerate(match):
                        print("  [%d] %s" % (i + 1, item.name))

                    while True:
                        ch = getch()
                        index = ord(ch) - ord("1")
                        if index >= 0 and index < len(match):
                            match = match[index]
                            break
                        else:
                            print2("(invalid key)")

                func_wrapper(match.func)


def file_is_old(src, dest):
    return not os.path.exists(dest) or os.path.getmtime(src) > os.path.getmtime(dest)


def format_time(sec):
    td = datetime.timedelta(seconds=sec)
    return "%02d:%02d:%02d,%03d" % (
        td.seconds // 3600,
        td.seconds // 60,
        td.seconds % 60,
        td.microseconds // 1000,
    )


def timing(f):
    def wrap(*args, **kwargs):
        time1 = time.time()
        ret = f(*args, **kwargs)
        time2 = time.time()
        print(
            "{:s} function took {:.3f} ms".format(f.__name__, (time2 - time1) * 1000.0)
        )

        return ret

    return wrap


def load_yaml(file: str):
    with open(file, "r", encoding="utf-8") as f:
        return yaml.load(f.read(), Loader=yaml.FullLoader)


def save_yaml(data, file: str):
    with open(file, "w", encoding="utf-8", newline="\n") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def update_yaml(file, dict_):
    data = load_yaml(file)
    data.update(dict_)
    save_yaml(data, file)


def setup_logger(level=logging.INFO, log_to_stdout=True, log_file=None):
    logger = logging.getLogger()
    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname).1s: %(name)s: %(message)s",
        "%H:%M:%S",
    )

    if log_to_stdout:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        handler.setLevel(level)
        logger.addHandler(handler)
    else:
        logger.propagate = False

    if log_file:
        file_handler = logging.FileHandler(
            log_file, "w+", encoding="utf-8"
        )  # overwrite the file
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

    return logger


if os.environ.get("_LOG"):
    setup_logger()
elif os.environ.get("_DEBUG"):
    setup_logger(level=logging.DEBUG)


def create_symlink(src, dst):
    assert os.path.isdir(src)
    subprocess.check_call(["MKLINK", "/J", dst, src], shell=True)


def to_valid_file_name(value):
    string_map = OrderedDict()
    string_map["<="] = "≤"
    string_map[">="] = "≥"
    string_map["<"] = "＜"
    string_map[">"] = "＞"
    string_map[":"] = "："
    string_map["\\"] = "＼"
    string_map["/"] = "／"
    string_map["*"] = "＊"
    string_map["|"] = "｜"
    string_map["?"] = "？"
    string_map['"'] = "”"

    for k, v in string_map.items():
        value = value.replace(k, v)

    return value


def input_with_default(message, default):
    print2("%s (e.g. %s): " % (message, default), color="green", end="")
    s = input()
    return s if s else default


def pause(msg="continue"):
    input(f"Press enter to {msg}...")


def keep_awake():
    if sys.platform == "win32":
        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        ES_DISPLAY_REQUIRED = 0x00000002
        ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
        )


def quote_arg(s, shell_type: str = "cmd"):
    if shell_type == "powershell":
        s = s.replace("(", r"`(").replace(")", r"`)")
    elif shell_type == "cmd":
        s = s.replace('"', '""')  # for cmd, we need to escape " with ""

    if " " in s or (shell_type != "cmd" and "\\" in s):
        s = '"' + s + '"'
    return s


def get_env_bool(name):
    if name in os.environ and os.environ[name].strip().isdigit():
        return int(os.environ[name]) > 0
    else:
        return None


def run_at_startup(name, cmdline):
    if sys.platform == "win32":
        args = [
            "reg",
            "add",
            "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run",
            "/v",
            name,
            "/t",
            "REG_SZ",
            "/d",
            cmdline,
            "/f",
        ]
        subprocess.check_output(args)
        logging.debug("run_at_startup(): %s" % args)


class IgnoreSigInt(object):
    def __enter__(self):
        self.original_handler = signal.getsignal(signal.SIGINT)

        def handler(signum, frame):
            pass

        signal.signal(signal.SIGINT, handler)
        return self

    def __exit__(self, type, value, tb):
        signal.signal(signal.SIGINT, self.original_handler)
