import ctypes
import datetime
import glob
import json
import locale
import logging
import os
import platform
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from collections import OrderedDict, namedtuple
from distutils.dir_util import copy_tree
from time import sleep
from typing import Dict

import yaml

logger = logging.getLogger(__name__)


def get_hash(text, digit=16):
    import hashlib

    hash_object = hashlib.md5(text.encode())
    hash = hash_object.hexdigest()[0:digit]
    return hash


def get_ahk_exe(uia=True):
    if uia:
        ahk_exe = os.path.expandvars(
            "%ProgramFiles%\\AutoHotkey\\AutoHotkeyU64_UIA.exe"
        )
    else:
        ahk_exe = "AutoHotkeyU64.exe"

    if not hasattr(get_ahk_exe, "init"):
        os.makedirs(os.path.expanduser("~\\Documents\\AutoHotkey"), exist_ok=True)
        run_elevated(
            r'cmd /c MKLINK /D "%USERPROFILE%\Documents\AutoHotkey\Lib" "{}"'.format(
                os.path.realpath(os.path.dirname(__file__) + "/../ahk")
            )
        )
        get_ahk_exe.init = True

    return ahk_exe


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
    assert os.name == "nt"
    if not tmp_script_path:
        tmp_script_path = write_temp_file(script, ".ahk")
    else:
        with open(tmp_script_path, "w", encoding="utf-8") as f:
            f.write("\ufeff")  # BOM utf-8
            f.write(script)
    run_ahk(tmp_script_path, wait=wait)


def wrap_args_conemu(args, title=None, cwd=None, wsl=False, always_on_top=False):
    assert sys.platform == "win32"

    CONEMU_INSTALL_DIR = r"C:\Program Files\ConEmu"

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

    if platform.system() == "Windows":
        import msvcrt
        import sys

        time_elapsed = 0
        if timeout > 0:
            while not msvcrt.kbhit() and time_elapsed < timeout:
                sleep(0.1)
                time_elapsed += 0.1
            return (
                msvcrt.getch().decode(errors="replace")
                if time_elapsed < timeout
                else None
            )
        else:
            return msvcrt.getch().decode(errors="replace")

    else:
        import sys
        import termios
        import tty

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


def cd(path, expand=True, auto_create_dir=False):
    if expand:
        path = os.path.expanduser(path)
        path = os.path.expandvars(path)

    path = os.path.realpath(path)

    if not os.path.exists(path):
        if auto_create_dir or yes('"%s" not exist, create?' % path):
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


def call_echo(args, shell=True, check=True, **kwargs):
    def quote(s):
        if " " in s:
            s = '"%s"' % s
        return s

    if type(args) == list:
        s = " ".join([quote(x) for x in args])
    else:
        s = args

    logger.debug("shell_cmd: %s" % s)
    print2("> " + s, color="black")
    ret = subprocess.run(args, shell=shell, check=check, **kwargs)
    return ret.returncode


def start_in_new_terminal(args, title=None):
    import shlex

    # Convert argument list to string
    if type(args) == list:
        args = [shlex.quote(x) for x in args]

    if platform.system() == "Windows":
        args = args.replace("|", "^|")  # Escape '|'
        title_arg = ('"' + title + '"') if title else ""
        args = 'start %s cmd /S /C "%s"' % (title_arg, args)
        subprocess.call(args, shell=True)

    elif platform.system() == "Darwin":
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
    if platform.system() == "Windows":
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


def download(url, filename=None, redownload=False):
    try:
        import requests
    except:
        subprocess.call([sys.executable, "-m", "pip", "install", "requests"])
        import requests

    if filename is None:
        filename = os.path.basename(url)

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
    # Create dirs if not exists
    dir_name = os.path.dirname(dst)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)

    if os.path.isdir(src):
        if dst.endswith("/"):
            dst = os.path.realpath(dst + os.path.basename(src))
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


def run_elevated(args, wait=True):
    if platform.system() == "Windows":
        import win32api
        import win32con
        import win32event
        import win32process
        from win32com.shell import shellcon
        from win32com.shell.shell import ShellExecuteEx

        if type(args) == str:
            lpFile, lpParameters = args.split(" ", 1)
        else:
            lpFile = args[0]
            lpParameters = subprocess.list2cmdline(args[1:])

        process_info = ShellExecuteEx(
            nShow=win32con.SW_SHOW,
            fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
            lpVerb="runas",
            lpFile=lpFile,
            lpParameters=lpParameters,
        )
        if wait:
            win32event.WaitForSingleObject(process_info["hProcess"], 600000)
            ret = win32process.GetExitCodeProcess(process_info["hProcess"])
            win32api.CloseHandle(process_info["hProcess"])
        else:
            ret = process_info
    else:
        ret = subprocess.call(["sudo"] + args, shell=True)
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


def proc_lines(args, echo=False, read_err=False, max_lines=None, check=True, **kwargs):
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

    ps = subprocess.Popen(
        args,
        stdout=subprocess.PIPE if (not read_err) else None,
        stderr=subprocess.PIPE if read_err else None,
        # bufsize=1,
        **kwargs
    )

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


def get_output(args, shell=True, **kwargs):
    return (
        subprocess.Popen(
            args, shell=shell, universal_newlines=True, stdout=subprocess.PIPE, **kwargs
        )
        .stdout.read()
        .strip()
    )


def print2(msg, color="yellow", end="\n"):
    # ANSI escape codes for colors
    COLOR_MAP = {
        "green": "\u001b[32;1m",
        "yellow": "\u001b[33;1m",
        "red": "\u001b[31;1m",
        "blue": "\u001b[34;1m",
        "magenta": "\u001b[35;1m",
        "cyan": "\u001b[36;1m",
        "black": "\u001b[30;1m",
        "YELLOW": "\u001b[43;1m",
        "RED": "\u001b[41;1m",
    }
    RESET = "\033[0m"

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

    for line in proc_lines(args, **kwargs):
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


def prepend_to_path(path, env=None):
    if env is None:
        env = os.environ

    if type(path) == list:
        path = [x for x in path if os.path.exists(x)]
        s = os.pathsep.join(path)
    elif type(path) == str:
        s = path
    else:
        raise ValueError()

    env["PATH"] = s + (os.pathsep + env["PATH"] if "PATH" in env else "")


def get_cur_time_str():
    return datetime.datetime.now().strftime("%y%m%d%H%M%S")


def exec_bash(script, wsl=False, echo=False):
    args = None
    if os.name == "nt":
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
    cur_folder = os.environ["_CUR_DIR"]

    if "_FILES" in os.environ:
        files = os.environ["_FILES"].split("|")
    else:
        files = list(glob.glob(os.path.join(cur_folder + "*.*")))

    files = sorted(files)

    if cd:
        os.chdir(cur_folder)
        files = [f.replace(cur_folder, "") for f in files]  # Relative path
        files = [x.lstrip(os.path.sep) for x in files]

    if ignore_dirs:
        files = [x for x in files if os.path.isfile(x)]
    return files


def get_selected_folder():
    files = os.environ["_FILES"].split("|")
    folders = [x for x in files if os.path.isdir(x)]
    return folders[0]


def get_current_folder():
    return os.environ["_CUR_DIR"]


def cd_current_dir():
    if "_CUR_DIR" in os.environ:
        os.chdir(os.environ["_CUR_DIR"])
    else:
        os.chdir(os.path.expanduser("~"))


def zip_file(path, out_file):
    shutil.make_archive(out_file.rstrip(".zip"), "zip", path)


def unzip(file, to=None):
    print('Unzip "%s"...' % file)
    import zipfile

    if to:
        mkdir(to)
    else:
        to = "."
    with zipfile.ZipFile(file, "r") as zip:
        zip.extractall(to)


def get_time_str():
    return datetime.datetime.now().strftime("%y%m%d_%H%M%S")


def make_and_change_dir(path):
    os.makedirs(path, exist_ok=True)
    os.chdir(path)


def get_pretty_mtime(file):
    dt = os.path.getmtime(file)
    now = time.time()
    seconds = int(dt - now)
    return get_pretty_time_delta(seconds)


def update_env_var_explorer():
    if sys.platform != "win32":
        return

    try:
        with open(os.path.join(os.environ["TEMP"], "ow_explorer_info.json")) as f:
            data = json.load(f)

        if data["current_folder"]:
            os.environ["_CUR_DIR"] = data["current_folder"]

        files = data["selected_files"]
        if not files:
            return None

        if len(files) == 1:
            os.environ["_FILE"] = files[0]

        if len(files) >= 1:
            os.environ["_FILES"] = "|".join(files)

        return files

    except:
        print("Unable to get explorer info.")
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
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_name])
        try_import(module_name)


def get_ip_addresses():
    return [
        info[4][0]
        for info in socket.getaddrinfo(socket.gethostname(), None)
        if info[0] == socket.AddressFamily.AF_INET
    ]


def check_output(args):
    out = subprocess.check_output(args)
    out = out.decode()
    return out


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


def add_to_path(path):
    if sys.platform == "win32":
        s = get_output(r"reg query HKCU\Environment /v PATH")
        s = re.search(r"PATH\s+(?:REG_SZ|REG_EXPAND_SZ)\s+(.*)", s).group(1).strip()
        paths = s.split(";")
        new_paths = []
        for p in paths:
            if os.path.isdir(p):
                new_paths.append(p)
            else:
                print("Removed from PATH: %s" % p)

        if path not in new_paths:
            new_paths.append(path)
            print("Added to PATH: %s" % path)

        subprocess.call(["setx", "PATH", ";".join(new_paths)])
        # call_echo('reg add HKCU\Environment /v PATH /d "%s" /f' % ";".join(new_paths))


def wait_key(prompt=None, timeout=5):
    if prompt is None:
        prompt = "Press enter to skip"
    print2(prompt, color="green", end="")
    ch = getch(timeout=timeout)
    print()
    return ch


def wait_until_file_modified(f):
    last_mtime = os.path.getmtime(f)
    while True:
        time.sleep(0.2)
        mtime = os.path.getmtime(f)
        if mtime > last_mtime:
            return


def start_process(args, shell=True):
    creationflags = 0
    if sys.platform == "win32":
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        DETACHED_PROCESS = 0x00000008
        creationflags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP

    with open(os.devnull, "w") as fnull:
        subprocess.Popen(
            args, shell=shell, stdout=fnull, stderr=fnull, creationflags=creationflags
        )


def setup_nodejs(install=True):
    if sys.platform == "win32":
        NODE_JS_PATH = r"C:\Program Files\nodejs"
        if install and not os.path.exists(NODE_JS_PATH):
            run_elevated("choco install nodejs -y")

        if os.path.exists(NODE_JS_PATH):
            print2("Node.js: %s" % NODE_JS_PATH)

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
        print2("NODE_PATH: %s" % node_path)

    else:
        print("setup_nodejs() not supported for current OS. Ignored.")


def npm_install(path="."):
    path = os.path.abspath(path)
    if not os.path.exists(os.path.join(path, "node_modules")):
        call_echo("yarn", cwd=path)


def get_next_file_name(file):
    POSTFIX_START = "-02"

    name, ext = os.path.splitext(file)
    basename = os.path.basename(name)
    folder = os.path.dirname(name)
    match = re.search("^(.*?)(\d*)$", basename)
    prefix = match.group(1)

    if match.group(2):
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


def yes(msg=""):
    msg += " (y/n): "
    print2(msg, end="", color="green")
    ch = getch()
    print()
    return ch == "y"


def shell_open(d="."):
    if sys.platform == "win32":
        os.startfile(d)
        # subprocess.Popen(['start', d], shell= True)

    elif sys.platform == "darwin":
        subprocess.Popen(["open", d])

    else:
        try:
            subprocess.Popen(["xdg-open", d])
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
        REG_PATH = [
            "HKLM\System\CurrentControlSet\Control\Session Manager\Environment",
            "HKCU\Environment",
        ]

        origin_path = os.environ["PATH"].split(";")

        # TODO: refresh other env variables
        for reg_path in REG_PATH:
            out = subprocess.check_output(
                'reg query "%s"' % reg_path, universal_newlines=True
            )
            lines = out.splitlines()
            lines = [x.strip() for x in lines if x.strip()]
            lines = lines[1:]  # Skip first line

            for line in lines:
                cols = line.split(maxsplit=2)
                if cols[0].upper() == "PATH":
                    path = cols[2]
                    path = path.split(";")

                    for p in path:
                        # Add to PATH if not exists
                        if p not in origin_path:
                            print("New PATH: %s" % p)
                            origin_path.append(p)


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


def slugify(s):
    import slugify as slug

    return slug.slugify(s)


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


def find_newest_file(wildcard):
    files = list(glob.glob(wildcard, recursive=True))
    files.sort(key=os.path.getmtime)
    return files[-1]


def move_file(src, dst, overwrite=False):
    dst = os.path.realpath(dst)
    assert os.path.exists(src)
    os.makedirs(os.path.dirname(dst), exist_ok=True)

    if overwrite and os.path.exists(dst):
        os.remove(dst)

    shutil.move(src, dst)


MenuItem = namedtuple("MenuItem", "name key func")
_menu_items: Dict[str, MenuItem] = {}


def menu_item(*, key, name=None):
    def decorator(func):
        nonlocal name
        if name is None:
            name = func.__name__

        if key in _menu_items:
            raise Exception("key '%s' is already used: %s" % (key, _menu_items.name))

        _menu_items[key] = MenuItem(name=name, key=key, func=func)

        return func

    return decorator


def menu_loop(run_periotic=None, interval=-1):
    def print_help():
        print2("Help Menu")
        print2("---------")

        for menu_item in sorted(_menu_items.values(), key=lambda x: x.name):
            print("  [%s] %s" % (menu_item.key, menu_item.name))

        print("  [h] help")
        print("  [q] quit")
        print()

    print_help()
    while True:
        if run_periotic is not None and interval > 0:
            while True:
                ch = getch(timeout=interval)
                if ch != None:
                    break
                else:
                    run_periotic()
        else:
            ch = getch()

        if ch == "h":
            print_help()
        elif ch == "q":
            break
        elif ch in _menu_items:
            try:
                _menu_items[ch].func()
            except Exception as ex:
                print2("Error: %s" % ex, color="red")
        else:
            print2("Invalid key: %s" % ch, color="yellow")


def file_is_old(in_file, out_file):
    return not os.path.exists(out_file) or os.path.getmtime(in_file) > os.path.getmtime(
        out_file
    )


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


def load_yaml(file):
    with open(file, "r", encoding="utf-8") as f:
        return yaml.load(f.read(), Loader=yaml.FullLoader)


def save_yaml(data, file):
    with open(file, "w", encoding="utf-8", newline="\n") as f:
        yaml.dump(
            data,
            f,
            default_flow_style=False,
            allow_unicode=True,
        )


def setup_logger(level=logging.DEBUG, log_file=None):
    logger = logging.getLogger()
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(name)s: %(levelname)s: %(message)s"))
    logger.addHandler(handler)

    if log_file:
        file_handler = logging.FileHandler(
            log_file,
            "w+",  # overwrite the file
        )
        file_handler.setLevel(level)
        logger.addHandler(file_handler)


def create_symlink(src, dst):
    assert os.path.isdir(src)
    subprocess.check_call(
        ["MKLINK", "/J", dst, src],
        shell=True,
    )


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
