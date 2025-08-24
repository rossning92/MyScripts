import ctypes
import functools
import glob
import json
import locale
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
from enum import IntEnum
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

from _android import setup_android_env
from _cpp import setup_cmake
from _filelock import FileLock
from _pkgmanager import require_package
from _shutil import (
    CONEMU_INSTALL_DIR,
    IgnoreSigInt,
    convert_to_unix_path,
    format_time,
    get_ahk_exe,
    get_home_path,
    get_hotkey_abbr,
    npm_install,
    prepend_to_path,
    print2,
    quote_arg,
    run_elevated,
    setup_nodejs,
    slugify,
    start_process,
    update_json,
    wrap_args_conemu,
    write_temp_file,
)
from scripting.path import (
    ScriptDirectory,
    get_absolute_script_path,
    get_bin_dir,
    get_data_dir,
    get_default_script_config_path,
    get_my_script_root,
    get_relative_script_path,
    get_script_alias,
    get_script_config_file,
    get_script_config_file_path,
    get_script_directories,
    get_script_dirs_config_file,
    get_script_history_file,
    get_temp_dir,
    get_variable_file,
)
from utils.clip import get_clip, get_selection
from utils.dotenv import load_dotenv
from utils.editor import open_code_editor
from utils.email import send_email_md
from utils.jsonutil import load_json, save_json
from utils.menu.csvmenu import CsvMenu
from utils.shutil import shell_open
from utils.template import render_template
from utils.term.alacritty import is_alacritty_installed, wrap_args_alacritty
from utils.term.windowsterminal import (
    DEFAULT_TERMINAL_FONT_SIZE,
    setup_windows_terminal,
)
from utils.timed import timed
from utils.tmux import is_in_tmux
from utils.venv import activate_python_venv, get_venv_python_executable
from utils.window import activate_window_by_name, close_window_by_name

SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))

SCRIPT_EXTENSIONS = {
    ".ahk",
    ".bat",
    ".c",
    ".cc",
    ".cmd",
    ".cpp",
    ".csv",
    ".expect",
    ".frag",  # shader
    ".glsl",  # shader
    ".ipynb",  # Python
    ".js",
    ".link",
    ".lua",
    ".md",
    ".mmd",  # mermaid source file
    ".ps1",
    ".py",
    ".scad",  # openscad
    ".sh",
    ".sql",
    ".tex",
    ".txt",
    ".url",
    ".vbs",  # Windows specific
}

BINARY_EXTENSIONS = {
    ".pdf",
}

if sys.platform == "win32":
    WINDOWS_TERMINAL_EXEC = (
        os.environ["LOCALAPPDATA"] + "\\Microsoft\\WindowsApps\\wt.exe"
    )

VARIABLE_NAME_EXCLUDE = {"HOME", "PATH"}


class BackgroundProcessOutputType(IntEnum):
    LOG_PIPE = 1
    REDIRECT_TO_FILE = 2


BG_PROCESS_OUTPUT_TYPE = BackgroundProcessOutputType.REDIRECT_TO_FILE


SUPPORT_GNU_SCREEN = False

DEFAULT_LINUX_TERMINAL = "alacritty"

MIGRATE_CONFIG_TO_JSON = True


def setup_env_var(env):
    root = get_my_script_root()

    paths = [os.path.join(root, "bin")]

    winget_links_dir = os.path.expanduser(r"%LOCALAPPDATA%\Microsoft\WinGet\Links")
    if os.path.exists(winget_links_dir):
        paths.append(winget_links_dir)

    prepend_to_path(paths, env=env)

    env["PYTHONPATH"] = os.path.join(root, "libs")
    env["MY_DATA_DIR"] = get_data_dir()
    env["MY_TEMP_DIR"] = get_temp_dir()

    _load_dotenv(env)


def add_script_dir(d, prefix=None):
    if prefix is None:
        prefix = "link/" + os.path.basename(d)

    config_file = get_script_dirs_config_file()
    data = load_json(config_file, default=[])
    # Remove existing item given by name
    data = [item for item in data if item["name"] != prefix]
    # Add new item
    data.append({"name": prefix, "directory": d})
    save_json(config_file, data)


def get_last_script_and_args() -> Tuple[str, Any]:
    if os.path.exists(get_script_history_file()):
        with open(get_script_history_file(), "r") as f:
            data = json.load(f)
            return data["file"], data["args"]
    else:
        raise ValueError("file cannot be None.")


def wrap_wsl(
    commands: Union[List[str], Tuple[str], str],
    env: Optional[Dict[str, str]],
    distro: Optional[str] = None,
) -> List[str]:
    if not os.path.exists(r"C:\Windows\System32\bash.exe"):
        raise Exception("WSL (Windows Subsystem for Linux) is not installed.")
    logging.debug("wrap_wsl(): cmd: %s" % commands)

    # To create a temp bash script to invoke commands to avoid command being parsed
    # by current shell
    bash = ""

    if env is not None:
        # Workaround: PATH environmental variable can't be shared between windows
        # and linux (WSL)
        if "PATH" in env:
            del env["PATH"]

        for k, v in env.items():
            bash += "export {}='{}'\n".format(k, v)

    if isinstance(commands, (list, tuple)):
        bash += _args_to_str(commands, shell_type="bash")
    else:
        bash += commands

    tmp_sh_file = write_temp_file(bash, ".sh")
    tmp_sh_file = convert_to_unix_path(tmp_sh_file, wsl=True)

    # # Escape dollar sign? Why?
    # commands = commands.replace("$", r"\$")
    # return ["bash.exe", "-c", commands]

    logging.debug("wrap_wsl(): write temp shell script: %s" % tmp_sh_file)
    return (
        [
            "wsl",
            "-d",
            distro,
            "bash",
        ]
        if distro
        else ["bash.exe"]
    ) + [
        # Ensures that .bashrc is read
        "-l",
        "-i",
        "-c",
        tmp_sh_file,
    ]


def wrap_bash_win(args: List[str], env: Optional[Dict[str, str]] = None, msys2=False):
    if env is not None:
        # https://www.msys2.org/wiki/MSYS2-introduction/#path
        env["MSYS_NO_PATHCONV"] = "1"  # Disable path conversion
        env["CHERE_INVOKING"] = "1"  # stay in the current working directory
        env["MSYSTEM"] = "MINGW64"
        env["HOME"] = get_home_path()
        # Export full PATH environment variable into MSYS2
        env["MSYS2_PATH_TYPE"] = "inherit"

    msys2_bash_search_list = []
    if msys2:
        msys2_bash_search_list += [
            r"C:\tools\msys64\usr\bin\bash.exe",
            r"C:\msys64\usr\bin\bash.exe",
        ]
    msys2_bash_search_list += [
        r"C:\Program Files\Git\bin\bash.exe",
    ]
    bash_exec = None
    for f in msys2_bash_search_list:
        if os.path.exists(f):
            bash_exec = f
            break
    logging.debug("bash_exec = %s" % bash_exec)

    if bash_exec is None:
        raise Exception("Cannot find MinGW bash.exe")

    if len(args) == 1 and args[0].endswith(".sh"):
        # -l: must start as a login shell otherwise the PATH environmental
        # variable is not correctly set up.
        return [bash_exec, "-l", args[0]]
    else:
        bash_cmd = _args_to_str(["bash"] + args, shell_type="bash")
        logging.debug("bash_cmd = %s" % bash_cmd)
        return [bash_exec, "-l", "-c", bash_cmd]


def wrap_bash_commands(
    args: List[str],
    wsl=False,
    wsl_distro: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    msys2=False,
) -> List[str]:
    if sys.platform == "win32":
        if wsl:  # WSL (Windows Subsystem for Linux)
            return wrap_wsl(args, env=env, distro=wsl_distro)
        else:
            return wrap_bash_win(args, env=env, msys2=msys2)

    else:  # Linux
        if len(args) == 1 and args[0].endswith(".sh"):
            return ["bash", args[0]]
        else:
            bash_cmd = "bash " + _args_to_str(args, shell_type="bash")
            logging.debug("bash_cmd = %s" % bash_cmd)
            return ["bash", "-c", bash_cmd]


def exec_cmd(cmd):
    assert sys.platform == "win32"
    file_name = write_temp_file(cmd, ".cmd")
    args = ["cmd.exe", "/c", file_name]
    subprocess.check_call(args)


def _args_to_str(args, shell_type):
    assert type(args) in [list, tuple]
    return " ".join([quote_arg(x, shell_type=shell_type) for x in args])


def get_all_variables() -> Dict[str, str]:
    file = get_variable_file()

    with FileLock("access_variable"):
        if not os.path.exists(file):
            return {}

        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)


def get_variable(name):
    with FileLock("access_variable"):
        f = get_variable_file()
        if not os.path.exists(f):
            return

        with open(get_variable_file(), "r") as f:
            variables = json.load(f)

        if name not in variables:
            return

        return variables[name]


def set_variable(name: str, val: str, set_env_var=True):
    logging.debug("set variable: %s=%s" % (name, val))
    assert val is not None

    with FileLock("access_variable"):
        file = get_variable_file()
        with open(file, "r", encoding="utf-8") as f:
            variables = json.load(f)

        variables[name] = val

        with open(file, "w", encoding="utf-8") as f:
            json.dump(variables, f, indent=2)

    if set_env_var:
        os.environ[name] = val


def set_variable_value(variables: Dict[str, str], name: str, value: str):
    variables[name] = value
    update_variables(variables)


def update_variables(variables: Dict[str, str]):
    config_file = get_variable_file()
    with FileLock("access_variable"):
        data = load_json(config_file, default={})
        data.update(variables)
        save_json(config_file, data)


def write_setting(setting, name, val):
    file = os.path.join(get_data_dir(), "%s.json" % setting)

    try:
        with open(file, "r") as f:
            data = json.load(f)
    except IOError:
        data = {}

    data[name] = val

    with open(file, "w") as f:
        json.dump(data, f, indent=2)


def get_python_path(script_path=None):
    python_path = []

    script_root = str(Path(__file__).resolve().parent.parent / "scripts")
    python_path.append(script_root)
    python_path.append(os.path.join(script_root, "r"))

    if script_path is not None:
        parent_dir = os.path.dirname(os.path.abspath(script_path))
        python_path.append(parent_dir)
        while parent_dir.startswith(script_root):
            python_path.append(parent_dir)
            parent_dir = os.path.abspath(parent_dir + "/../")

    python_path.append(SCRIPT_ROOT)

    return list(set(python_path))


def setup_python_path(env, script_path=None, wsl=False):
    python_path = get_python_path(script_path)
    if wsl:
        python_path = [convert_to_unix_path(x, wsl=True) for x in python_path]
        python_path = ":".join(python_path)
    else:
        python_path = os.pathsep.join(python_path)

    logging.debug("setup_python_path(): %s" % python_path)
    env["PYTHONPATH"] = python_path


def wrap_args_tee(args, out_file):
    assert isinstance(args, list)

    if sys.platform == "win32":
        s = (
            # Powershell uses UTF-16 as default encoding, make tee output UTF-8
            "$PSDefaultParameterValues = @{'Out-File:Encoding' = 'utf8'}; & "
            + _args_to_str(args, shell_type="powershell")
            + r" | Tee-Object -FilePath %s" % out_file
        )
        tmp_file = write_temp_file(s, ".ps1")
        logging.debug('wrap_args_tee(file="%s"): %s' % (tmp_file, s))
        return ["powershell", tmp_file]
    else:
        return args


def wrap_args_cmd(args: List[str], title=None, cwd=None, env=None) -> str:
    if sys.platform == "win32":
        cmdline = "cmd /c "
        if title:
            cmdline += "title %s&" % quote_arg(title)
        if cwd:
            cmdline += "cd /d %s&" % quote_arg(cwd)
        if env:
            for k, v in env.items():
                cmdline += "&".join(['set "%s=%s"' % (k, v)]) + "&"
        cmdline += _args_to_str(args, shell_type="cmd")
    else:
        cmdline = ""
        for k, v in env.items():
            if k != "PATH":
                cmdline += "%s=%s" % (k, v) + " "
        cmdline += _args_to_str(args, shell_type="bash")

    return cmdline


def wrap_args_wt(
    args,
    title=None,
    font_size=DEFAULT_TERMINAL_FONT_SIZE,
    opacity=1.0,
    **kwargs,
) -> List[str]:
    if sys.platform != "win32":
        raise Exception("OS not supported.")

    setup_windows_terminal(font_size=font_size, opacity=opacity)

    if title:
        return [WINDOWS_TERMINAL_EXEC, "--title", title] + args
    else:
        return [WINDOWS_TERMINAL_EXEC] + args


class LogPipe(threading.Thread):
    def __init__(self, read_pipe, log_level):
        threading.Thread.__init__(self)
        self.daemon = False
        self.level = log_level
        self.read_pipe = read_pipe
        self.start()

    def log(self):
        for line in iter(self.read_pipe.readline, b""):
            logging.log(self.level, ">>> " + line.strip(b"\n").decode())

        self.read_pipe.close()

    def run(self):
        self.log()


@functools.lru_cache(maxsize=None)
def install_pip_packages(pkg: str, python_exec: str) -> None:
    # Check if pip package is installed
    ret = subprocess.call(
        [
            python_exec,
            "-c",
            f"import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('{pkg}') else 1)",
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if ret != 0:
        print(f"{pkg} is not found, installing...")
        subprocess.check_call([python_exec, "-m", "pip", "install", pkg])


class Script:
    def __init__(self, script_path: str, name=None):
        self.__cached_source: Optional[str] = None

        if os.path.isfile(script_path):
            script_path = os.path.abspath(script_path)
        else:
            matched_script = find_script(script_path)
            if matched_script:
                script_path = matched_script
            else:
                raise Exception("Script file does not exist.")

        self.script_rel_path = get_relative_script_path(script_path)

        # Script display name
        if name:
            self.name = name
        else:
            self.name = self.script_rel_path

        root, ext = os.path.splitext(script_path)

        self.alias = get_script_alias(root)
        self.ext = ext.lower()
        self.override_variables = None
        self.console_title = None
        self.script_path = script_path
        self.ps: Optional[subprocess.Popen] = None

        # Deal with links
        if os.path.splitext(script_path)[1].lower() == ".link":
            self.real_script_path: Optional[str] = (
                open(script_path, "r", encoding="utf-8").read().strip()
            )
            self.real_ext: Optional[str] = os.path.splitext(self.real_script_path)[
                1
            ].lower()

            self.check_link_existence()
        else:
            self.real_script_path = None
            self.real_ext = None

        self.mtime = 0.0
        self.refresh_script()

    def clear_source_cache(self):
        self.__cached_source = None

    def match_pattern(self, text: str) -> Optional[re.Match]:
        patt = self.cfg["matchClipboard"]
        return re.search(patt, text) if patt else None

    def is_running(self) -> bool:
        return self.ps is not None and self.ps.poll() is None

    def __lt__(self, other):
        return self.mtime > other.mtime  # sort by modified time descendently by default

    def refresh_script(self) -> bool:
        assert self.script_path

        mtime = os.path.getmtime(self.script_path)

        script_config_file = get_script_config_file(self.script_path)
        if script_config_file:
            mtime = max(mtime, os.path.getmtime(script_config_file))
        default_script_config_file = get_default_script_config_path(self.script_path)
        if os.path.exists(default_script_config_file):
            mtime = max(mtime, os.path.getmtime(default_script_config_file))

        if mtime > self.mtime:
            self.mtime = mtime

            # Reload script config
            self.cfg = self.load_config()

            return True
        else:
            return False

    def __str__(self):
        s = self.name

        # Link
        if self.ext == ".link":
            s = "%s (lnk)"

        # Show keyboard shortcut
        if self.cfg["globalHotkey"]:
            s += " {%s}" % (get_hotkey_abbr(self.cfg["globalHotkey"]))
        if self.cfg["hotkey"]:
            s += " [%s]" % (get_hotkey_abbr(self.cfg["hotkey"]))
        if self.alias:
            s += f" ({self.alias})"

        if self.cfg["autoRun"]:
            s += " @autorun"
        if self.cfg["runAtStartup"]:
            s += " @startup"

        return s

    def load_config(self):
        return load_script_config(
            self.real_script_path
            if self.real_script_path is not None
            else self.script_path
        )

    def check_link_existence(self):
        if self.real_script_path is not None:
            if not os.path.exists(self.real_script_path):
                print2("WARNING: cannot locate the link: %s" % self.name)
                # os.remove(self.script_path)
                return False
        return True

    def get_window_title(self) -> str:
        if self.console_title:
            return self.console_title
        elif self.cfg["title"]:
            assert isinstance(self.cfg["title"], str)
            return self.cfg["title"]
        else:
            return "!!" + self.name

    def get_window_name_tmux(self) -> str:
        if self.console_title:
            return self.console_title
        elif self.cfg["title"]:
            assert isinstance(self.cfg["title"], str)
            return self.cfg["title"]
        else:
            return os.path.splitext(os.path.basename(self.script_path))[0]

    def get_script_path(self) -> str:
        return self.real_script_path if self.real_script_path else self.script_path

    def get_script_source(self) -> str:
        if self.__cached_source:
            return self.__cached_source

        if self.ext in [".bat", ".cmd"]:
            encoding = locale.getpreferredencoding()
        else:
            encoding = "utf-8"

        script_path = self.get_script_path()
        with open(script_path, "r", encoding=encoding) as f:
            source = f.read()

        self.__cached_source = source
        return self.__cached_source

    def render(
        self,
        variables: Optional[Dict] = None,
    ) -> str:
        read_var_from_csv = self.cfg["template.readVarFromCsv"]
        assert isinstance(read_var_from_csv, str)

        if read_var_from_csv:
            menu = CsvMenu(csv_file=read_var_from_csv)
            row_index = menu.select_row()
            if row_index >= 0:
                variables = {
                    k.upper(): v for k, v in menu.df.get_row_dict(row_index).items()
                }

        else:
            if variables is None:
                variables = self.get_variables()

        if not self.check_link_existence():
            raise Exception("Link is invalid.")

        result = render_template(
            self.get_script_source(), variables, file_locator=find_script
        )

        return result

    def set_override_variables(self, variables):
        self.override_variables = variables

    def get_variables(self) -> Dict[str, str]:
        vnames = self.get_variable_names()
        saved_variables = get_all_variables()

        # Get all variables for the script
        variables = {}
        for vname in vnames:
            if vname in saved_variables:
                last_modified_value = saved_variables[vname]
                # Note that last_modified_value can be an empty string
                variables[vname] = last_modified_value
            else:
                variables[vname] = ""

        variables["MYSCRIPT_ROOT"] = get_my_script_root()

        # Override variables
        if self.override_variables:
            variables = {**variables, **self.override_variables}

        # Convert into private namespace (shorter variable name)
        prefix = self.get_public_variable_prefix()
        variables = {
            **variables,
            **{
                k[len(prefix) :]: v
                for k, v in variables.items()
                if k.startswith(prefix + "_")
            },
        }

        # Variables can be overridden by environmental variables
        for name in variables.keys():
            if name in os.environ:
                val = os.environ[name]
                variables[name] = val
                logging.debug("Override variable by env var: %s=%s" % (name, val))

        return variables

    def get_public_variable_prefix(self):
        return os.path.splitext(os.path.basename(self.script_path))[0].upper()

    def convert_private_variables(self, variables):
        prefix = self.get_public_variable_prefix()
        return {
            (prefix + k if k.startswith("_") else k): v for k, v in variables.items()
        }

    def get_userscript_url(self) -> str:
        return "http://127.0.0.1:4312/fs/" + self.script_path.replace(os.path.sep, "/")

    def is_supported(self) -> bool:
        if ".win" in self.script_path and sys.platform != "win32":
            return False
        if ".linux" in self.script_path and sys.platform != "linux":
            return False
        if ".mac" in self.script_path and sys.platform != "darwin":
            return False
        if self.ext == ".ahk" and sys.platform != "win32":
            return False
        return True

    def get_short_name(self) -> str:
        return os.path.splitext(os.path.basename(self.name))[0]

    def get_context(self) -> Dict[str, str]:
        return {
            **self.get_variables(),
            "HOME": get_home_path(),
            "SCRIPT": quote_arg(self.script_path),
        }

    def activate_window(self) -> bool:
        title = self.get_window_title()
        if (
            is_in_tmux()
            and subprocess.call(
                ["tmux", "select-window", "-t", self.get_window_name_tmux()],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            == 0
        ):
            return True
        elif (
            SUPPORT_GNU_SCREEN
            and shutil.which("screen")
            and subprocess.call(["screen", "-r", slugify(title)]) == 0
        ):
            return True

        elif activate_window_by_name(title):
            logging.info(f"Activated window by title: {title}")
            return True

        else:
            return False

    def close_window(self):
        if (
            SUPPORT_GNU_SCREEN
            and shutil.which("screen")
            and subprocess.call(
                [
                    "screen",
                    "-S",
                    slugify(self.get_window_title()),
                    "-X",
                    "quit",
                ]
            )
            == 0
        ):
            pass

        elif is_in_tmux():
            subprocess.call(["tmux", "kill-window", "-t", self.get_window_name_tmux()])

        else:
            # Close exising instances
            close_window_by_name(self.get_window_title())

    def get_script_log_file(self) -> str:
        log_dir = os.path.join(get_data_dir(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, slugify(self.get_window_title())) + ".log"
        return log_file

    def execute(
        self,
        args: List[str] = [],
        new_window: Optional[bool] = None,
        single_instance=None,
        restart_instance=False,
        close_on_exit=None,
        cd=True,
        tee=None,
        command_wrapper: Optional[bool] = None,
        background=False,
        out_to_file: Optional[str] = None,
        run_script_local=False,
    ) -> bool:
        self.clear_source_cache()

        if not self.is_supported():
            logging.warning(f"{self.name} is not supported on {sys.platform}.")
            return False

        script_path = self.get_script_path()
        ext = self.real_ext if self.real_ext else self.ext

        # If this is not a text/script file
        if self.ext not in SCRIPT_EXTENSIONS:
            shell_open(self.get_script_path())
            return True

        self.cfg = self.load_config()

        assert isinstance(self.cfg["newWindow"], bool)
        new_window = self.cfg["newWindow"] if new_window is None else new_window

        background = background or self.cfg["background"]

        if single_instance is None:
            single_instance = self.cfg["singleInstance"]

        if tee is None:
            tee = self.cfg["tee"]

        if self.cfg["restartInstance"]:
            restart_instance = True

        if new_window and not restart_instance and single_instance:
            if self.activate_window():
                return True

        # Get variable name value pairs
        variables = self.get_variables()

        # Override environment variable with user input.
        if self.cfg["env.userInput"]:
            from utils.menu.inputmenu import InputMenu

            assert isinstance(self.cfg["env.userInput"], str)
            env_var_names = self.cfg["env.userInput"].split()
            for name in env_var_names:
                val = InputMenu(prompt="input " + name).request_input()
                if not val:
                    return True
                variables[name] = val

        logging.info(
            "execute: %s %s"
            % (self.name, _args_to_str(args, shell_type="bash") if args else "")
        )

        close_on_exit = (
            close_on_exit if close_on_exit is not None else self.cfg["closeOnExit"]
        )
        logging.debug(f"close_on_exit={close_on_exit}")

        arg_list = args

        # If no arguments is provided to the script, try to provide the default
        # values from the script config.
        if len(arg_list) == 0:
            if self.cfg["args"]:
                arg_list += self.cfg["args"].split()

            if self.cfg["args.selectionAsFile"]:
                selection = get_selection()
                temp_file = write_temp_file(selection, ".txt")
                arg_list.append(temp_file)

            elif self.cfg["args.userInput"]:
                from utils.menu.inputmenu import InputMenu

                text = InputMenu().request_input()
                if not text:
                    return True
                arg_list.append(text)

            elif self.cfg["args.selection"]:
                selection = get_selection()
                arg_list.append(selection)

            elif self.cfg["args.clipboard"]:
                clipboard = get_clip()
                arg_list.append(clipboard)

            elif self.cfg["args.clipboardAsFile"]:
                clipboard = get_clip()
                temp_file = write_temp_file(clipboard, ".txt")
                arg_list.append(temp_file)

            elif self.cfg["args.selectFiles"]:
                from utils.menu.filemenu import FileMenu

                files = FileMenu().select_files()
                if len(files) == 0:
                    return True
                arg_list.extend(files)

            elif self.cfg["args.selectDir"]:
                from utils.menu.filemenu import FileMenu

                file = FileMenu().select_directory()
                if file is None:
                    return True
                else:
                    arg_list.append(file)

        # Load dotenv
        dotenv: Dict[str, str] = {}
        _load_dotenv(dotenv)

        # Set up environment variables for the new process
        env = {**variables, **dotenv}

        # Set proxy settings
        proxy_settings = load_json(
            os.path.join(get_data_dir(), "proxy_settings.json"),
            default={"http_proxy": ""},
        )
        if proxy_settings["http_proxy"]:
            env["http_proxy"] = proxy_settings["http_proxy"]

        shell = False
        use_shell_execute_win32 = False

        if self.cfg["adk"]:
            setup_android_env(
                env=env,
                jdk_version=self.cfg["adk.jdk_version"],
                android_home=(
                    variables["ANDROID_HOME"] if "ANDROID_HOME" in variables else None
                ),
            )

        if self.cfg["cmake"]:
            setup_cmake(env=env, cmake_version=self.cfg["cmake.version"])

        setup_env_var(env)

        # Setup PYTHONPATH globally (e.g. useful for vscode)
        setup_python_path(env)

        # Check if template is enabled or not
        if self.cfg["template"] is None:
            template = "{{" in self.get_script_source()
        else:
            template = self.cfg["template"]
        logging.debug(f"template={template}")

        # HACK: pass current folder
        if "CWD" in os.environ:
            env["CWD"] = os.environ["CWD"]

        # Override ANDROID_SERIAL
        if "ANDROID_SERIAL" not in os.environ:
            android_serial = get_variable("ANDROID_SERIAL")
            if android_serial:
                env["ANDROID_SERIAL"] = android_serial

        cwd = None
        if cd:
            # If custom working dir is specified.
            if self.cfg["workingDir"]:
                working_dir = self.cfg["workingDir"]
                assert isinstance(working_dir, str)
                working_dir = working_dir.format(**self.get_context())
                if working_dir:
                    cwd = working_dir
                    if not os.path.exists(cwd):
                        os.makedirs(cwd, exist_ok=True)

            # Default to set working directory to script dir.
            if cwd is None:
                cwd = os.path.abspath(
                    os.path.join(os.getcwd(), os.path.dirname(script_path))
                )

        if "CWD" in os.environ:
            cwd = os.environ["CWD"]
        logging.debug("CWD = %s" % cwd)

        # Automatically convert path arguments to UNIX path if running in WSL
        if sys.platform == "win32" and self.cfg["wsl"]:
            arg_list = [convert_to_unix_path(x, wsl=self.cfg["wsl"]) for x in arg_list]

        if self.cfg["runRemotely"]:
            from utils.remoteshell import run_bash_script_in_remote_shell

            run_bash_script_in_remote_shell(self.get_script_path())
            return True

        cmdline = self.cfg["cmdline"]
        if cmdline:
            arg_list = shlex.split(cmdline.format(**self.get_context())) + arg_list

        elif not run_script_local and self.cfg["openWithScript"]:
            arg_list = [
                "run_script",
                self.cfg["openWithScript"],
                script_path,
            ] + arg_list

        elif not run_script_local and self.cfg["runOverSsh"]:
            arg_list = [
                sys.executable,
                find_script("ext/run_script_ssh.py"),
                script_path,
            ]

        elif ext in [".md", ".txt"]:
            if script_path.endswith(".email.md"):
                send_email_md(content=self.render(variables=variables))
            else:
                if template:
                    script_path = write_temp_file(
                        self.render(variables=variables),
                        slugify(self.name) + ext,
                    )
                    md_file_path = script_path
                else:
                    md_file_path = script_path
                open_code_editor(md_file_path)
                return True

        elif ext == ".ps1":
            if sys.platform == "win32":
                if template:
                    ps_path = write_temp_file(
                        self.render(variables=variables),
                        slugify(self.name) + ".ps1",
                    )
                else:
                    ps_path = os.path.abspath(script_path)

                arg_list = [
                    "PowerShell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "unrestricted",
                    "-file",
                    ps_path,
                ] + arg_list
            else:
                print("ERROR: OS does not support script: %s" % script_path)
                return False

        elif ext == ".ahk":
            if sys.platform == "win32":
                # HACK: add python path to env var
                env["PYTHONPATH"] = SCRIPT_ROOT

                if template:
                    script_path = write_temp_file(
                        self.render(variables=variables),
                        os.path.join(
                            "GeneratedAhkScript/", os.path.basename(self.script_path)
                        ),
                    )
                else:
                    script_path = os.path.abspath(script_path)

                arg_list = [get_ahk_exe(), script_path]

                if self.cfg["runAsAdmin"]:
                    arg_list = ["start"] + arg_list

                # Disable console window for ahk
                new_window = False
                background = True

                # Avoid WinError 740: The requested operation requires elevation
                # for AutoHotkeyU64_UIA.exe
                shell = True
                use_shell_execute_win32 = True

        elif ext == ".cmd" or ext == ".bat":
            if sys.platform == "win32":
                if template:
                    batch_file = write_temp_file(
                        self.render(variables=variables),
                        slugify(self.name) + ".cmd",
                    )
                else:
                    batch_file = os.path.abspath(script_path)

                # "call" must be used if there are spaces in batch file name
                arg_list = ["cmd.exe", "/c", "call", batch_file] + arg_list
            else:
                print("ERROR: OS does not support script: %s" % script_path)
                return False

        elif ext == ".js":
            # Userscript
            if script_path.endswith(".user.js"):
                user_script_path = self.script_path
                if template:
                    user_script_path = os.path.dirname(user_script_path)
                    if len(user_script_path) > 0:
                        user_script_path += "/"
                    user_script_path += "generated/" + os.path.basename(
                        self.script_rel_path
                    )
                    d = os.path.join(os.path.dirname(self.script_path), "generated")
                    os.makedirs(d, exist_ok=True)
                    with open(
                        os.path.join(d, os.path.basename(self.script_path)),
                        "w",
                        encoding="utf-8",
                    ) as f:
                        f.write(self.render(variables=variables))

                url = "http://127.0.0.1:4312/fs/" + user_script_path.replace(
                    os.path.sep, "/"
                )
                logging.info(f"Open user script in browser: {url}")
                shell_open(url)

            else:
                # TODO: support template for js files
                setup_nodejs()
                npm_install(cwd=os.path.dirname(script_path))
                arg_list = ["node", script_path] + arg_list

        elif ext == ".sh":
            if template:
                script_path = write_temp_file(
                    self.render(variables=variables),
                    slugify(self.name) + ".sh",
                )

            arg_list = [script_path] + arg_list
            arg_list = [
                convert_to_unix_path(arg, wsl=self.cfg["wsl"]) for arg in arg_list
            ]

            if sys.platform == "win32" and self.cfg["msys2"]:
                require_package("msys2")

            arg_list = wrap_bash_commands(
                arg_list,
                wsl=self.cfg["wsl"],
                wsl_distro=self.cfg["wsl.distro"],
                env=env,
                msys2=self.cfg["msys2"],
            )

        elif ext == ".expect":
            arg_list = wrap_bash_commands(
                ["expect", convert_to_unix_path(script_path, wsl=True)],
                wsl=True,
                wsl_distro=self.cfg["wsl.distro"],
                env=env,
            )

        elif ext == ".py" or ext == ".ipynb":
            if self.cfg["venv.name"]:
                python_exec = get_venv_python_executable(self.cfg["venv.name"])
            else:
                python_exec = sys.executable

            if template and ext == ".py":
                python_file = write_temp_file(
                    self.render(variables=variables),
                    slugify(self.name) + ".py",
                )
            else:
                python_file = os.path.abspath(script_path)

            if sys.platform == "win32" and self.cfg["wsl"]:
                python_file = convert_to_unix_path(python_file, wsl=self.cfg["wsl"])
                python_exec = "python3"

            setup_python_path(env, script_path, wsl=self.cfg["wsl"])
            # env["PYTHONDONTWRITEBYTECODE"] = "1"

            # Conda / venv support
            args_activate = []
            if self.cfg["conda"]:
                assert sys.platform == "win32"
                import _conda

                env_name = self.cfg["conda"]
                conda_path = _conda.get_conda_path()

                activate = conda_path + "\\Scripts\\activate.bat"

                if env_name != "base" and not os.path.exists(
                    conda_path + "\\envs\\" + env_name
                ):
                    subprocess.check_call(
                        'call "%s" & conda create --name %s python=3.6'
                        % (activate, env_name)
                    )

                args_activate = ["cmd", "/c", "call", activate, env_name, "&"]

            # Install pip packages
            config_packages_pip = self.cfg["packages.pip"]
            assert isinstance(config_packages_pip, str)
            for pkg in config_packages_pip.split():
                install_pip_packages(pkg, python_exec=python_exec)

            if ext == ".py":
                if self.cfg["runpy"]:
                    run_py = os.path.abspath(SCRIPT_ROOT + "/../bin/run_python.py")
                    # TODO: make it more general
                    if sys.platform == "win32":
                        if self.cfg["wsl"]:
                            run_py = convert_to_unix_path(run_py, wsl=self.cfg["wsl"])

                    # -u disables buffering so that we can get correct output
                    # during piping output
                    arg_list = (
                        args_activate
                        + [python_exec, "-u", run_py, python_file]
                        + arg_list
                    )
                else:
                    arg_list = (
                        args_activate + [python_exec, "-u", python_file] + arg_list
                    )
            elif ext == ".ipynb":
                arg_list = (
                    args_activate + ["jupyter", "notebook", python_file] + arg_list
                )

                # HACK: always use new window for jupyter notebook
                self.cfg["newWindow"] = True
            else:
                assert False

            if sys.platform == "win32" and self.cfg["wsl"]:
                arg_list = wrap_wsl(arg_list, env=env)
        elif ext == ".vbs":
            assert sys.platform == "win32"

            script_abs_path = os.path.join(os.getcwd(), script_path)
            arg_list = ["cscript", "//nologo", script_abs_path] + arg_list

        elif ext == ".cpp" or ext == ".c" or ext == ".cc":
            arg_list = ["run_script", "ext/build_and_run_cpp.py", script_path]

        elif ext == ".csv":
            arg_list = [sys.executable, find_script("r/csv/csvviewer.py"), script_path]

        elif ext == ".url":
            if template:
                url = self.render(variables=variables)
            else:
                url = self.get_script_source()

            if "%s" in url:
                from utils.menu.inputmenu import InputMenu

                if len(arg_list) == 1:
                    keyword = arg_list[0]
                else:
                    keyword = InputMenu(
                        show_clipboard=True, return_selection_if_empty=True
                    ).request_input()
                    if not keyword:
                        return True
                url = url.replace("%s", urllib.parse.quote(keyword))

            fallback_to_shell_open = True
            if self.cfg["webApp"]:
                chrome_executables = ["google-chrome-stable", "google-chrome", "chrome"]
                if sys.platform == "win32":
                    chrome_executables.insert(
                        0, r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                    )
                for chrome_exec in chrome_executables:
                    if shutil.which(chrome_exec):
                        args = [chrome_exec, f"--app={url}"]
                        start_process(args)
                        fallback_to_shell_open = False
                        break

            if fallback_to_shell_open:
                shell_open(url)
            return True

        else:
            print("ERROR: not supported script extension: %s" % ext)

        # venv
        if self.cfg["venv.name"]:
            activate_python_venv(self.cfg["venv.name"], env)
        else:
            # If Python is running in a virtual environment (venv), ensure that the
            # shell executes the Python version located inside the venv.
            prepend_to_path(os.path.dirname(sys.executable))

        # Install dependant packages
        if self.cfg["packages"]:
            packages = self.cfg["packages"].split()
            for pkg in packages:
                require_package(pkg, wsl=self.cfg["wsl"], env=env)

            if "node" in packages:
                print("node package is required.")
                setup_nodejs(install=False)

        # Run commands
        if len(arg_list) > 0:
            if tee:
                out_dir = os.path.join(get_home_path(), "Desktop")
                os.makedirs(out_dir, exist_ok=True)
                log_file = os.path.join(
                    out_dir,
                    "{}_{}.log".format(self.get_short_name(), int(time.time())),
                )
                logging.debug(f"log_file: {log_file}")
                arg_list = [
                    sys.executable,
                    os.path.join(get_my_script_root(), "scripts", "r", "logviewer.py"),
                    "--output",
                    log_file,
                    "--cmdline",
                ] + arg_list

            no_wait = False
            open_in_terminal = False
            popen_extra_args: Dict[str, Any] = {}

            if command_wrapper is None:
                command_wrapper = self.cfg["commandWrapper"]
            logging.debug(f"command_wrapper={command_wrapper}")

            if (
                command_wrapper
                and not (background or out_to_file)
                and not self.cfg["minimized"]
            ):
                # Add command wrapper to pause on exit
                env["CMDW_CLOSE_ON_EXIT"] = "1" if close_on_exit else "0"
                env["CMDW_WINDOW_TITLE"] = self.get_window_title()
                arg_list = [
                    sys.executable,
                    os.path.join(get_bin_dir(), "command_wrapper.py"),
                ] + arg_list

            if background or out_to_file:
                logging.debug("background = true")

                if sys.platform == "win32":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
                    SW_HIDE = 0
                    startupinfo.wShowWindow = SW_HIDE
                    popen_extra_args["startupinfo"] = startupinfo

                    CREATE_NO_WINDOW = 0x08000000
                    # A detached process is a child process that runs
                    # independently of its parent process. It is not associated
                    # with the parent process and does not receive any signals
                    # or notifications from it. Once the parent process
                    # terminates, the detached process continues to run,
                    # unaffected by the termination of the parent.
                    DETACHED_PROCESS = 0x00000008
                    popen_extra_args["creationflags"] = (
                        # DETACHED_PROCESS
                        CREATE_NO_WINDOW
                        | subprocess.CREATE_NEW_PROCESS_GROUP
                    )

                if BG_PROCESS_OUTPUT_TYPE == BackgroundProcessOutputType.LOG_PIPE:
                    popen_extra_args["stdin"] = subprocess.DEVNULL
                    popen_extra_args["stdout"] = subprocess.PIPE
                    popen_extra_args["stderr"] = subprocess.PIPE

                elif (
                    BG_PROCESS_OUTPUT_TYPE
                    == BackgroundProcessOutputType.REDIRECT_TO_FILE
                ):
                    fd = open(
                        (out_to_file if out_to_file else self.get_script_log_file()),
                        "w",
                    )
                    popen_extra_args["stdin"] = subprocess.DEVNULL
                    popen_extra_args["stdout"] = fd
                    popen_extra_args["stderr"] = fd

                else:
                    popen_extra_args["stdin"] = subprocess.DEVNULL
                    popen_extra_args["stdout"] = subprocess.DEVNULL
                    popen_extra_args["stderr"] = subprocess.DEVNULL
                    popen_extra_args["close_fds"] = True
                no_wait = True

            elif sys.platform == "win32" and self.cfg["minimized"]:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
                SW_MINIMIZE = 6
                startupinfo.wShowWindow = SW_MINIMIZE
                popen_extra_args["startupinfo"] = startupinfo

                popen_extra_args["creationflags"] = (
                    subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP
                )
                popen_extra_args["close_fds"] = True
                no_wait = True

            elif new_window:
                if restart_instance and single_instance:
                    self.close_window()

                try:
                    if sys.platform == "win32":
                        # Open in specified terminal (e.g. Windows Terminal)
                        if self.cfg["terminal"] in [
                            "wt",
                            "wsl",
                            "windowsTerminal",
                        ] and os.path.exists(WINDOWS_TERMINAL_EXEC):
                            arg_list = wrap_args_wt(
                                arg_list,
                                cwd=cwd,
                                title=self.get_window_title(),
                                wsl=self.cfg["wsl"],
                            )
                            no_wait = True
                            open_in_terminal = True

                        elif self.cfg["terminal"] == "alacritty" and shutil.which(
                            "alacritty"
                        ):
                            arg_list = wrap_args_alacritty(
                                arg_list,
                                title=self.get_window_title(),
                            )

                            # Workaround: prevent Alacritty from being closed by parent terminal. The "shell = True"
                            # below is very important!
                            popen_extra_args["creationflags"] = (
                                subprocess.CREATE_NO_WINDOW
                            )
                            popen_extra_args["close_fds"] = True
                            shell = True
                            no_wait = True
                            open_in_terminal = True

                        elif self.cfg["terminal"] == "conemu" and os.path.isdir(
                            CONEMU_INSTALL_DIR
                        ):
                            arg_list = wrap_args_conemu(
                                arg_list,
                                cwd=cwd,
                                title=self.get_window_title(),
                                wsl=self.cfg["wsl"],
                                always_on_top=True,
                            )
                            no_wait = True
                            open_in_terminal = True

                        else:
                            logging.warning(
                                "No terminal installed, ignore `newWindow` option."
                            )

                    elif is_in_tmux():
                        arg_list = (
                            [
                                "tmux",
                                # "split-window",
                                "new-window",
                                "-n",
                                self.get_window_name_tmux(),
                            ]
                            + [  # Pass environmental variable to new window.
                                item
                                for k, v in env.items()
                                for item in ("-e", f"{k}={v}")
                            ]
                            + arg_list
                        )

                    elif sys.platform == "linux":
                        if os.environ.get("DISPLAY"):
                            term_emulator = DEFAULT_LINUX_TERMINAL
                            if term_emulator == "gnome":
                                arg_list = [
                                    "gnome-terminal",
                                    "--",
                                    "bash",
                                    "-c",
                                    "%s || read -rsn1 -p 'Press any key to exit...'"
                                    % _args_to_str(arg_list, shell_type="bash"),
                                ]

                            elif term_emulator == "xterm":
                                arg_list = [
                                    "xterm",
                                    "-xrm",
                                    "XTerm.vt100.allowTitleOps: false",
                                    "-T",
                                    self.get_window_title(),
                                    "-e",
                                    _args_to_str(arg_list, shell_type="bash"),
                                ]
                                no_wait = True
                                open_in_terminal = True

                            elif term_emulator == "xfce":
                                arg_list = [
                                    "xfce4-terminal",
                                    "-T",
                                    self.get_window_title(),
                                    "-e",
                                    _args_to_str(arg_list, shell_type="bash"),
                                    "--hold",
                                ]
                                no_wait = True
                                open_in_terminal = True

                            elif term_emulator == "kitty":
                                arg_list = [
                                    "kitty",
                                    "--title",
                                    self.get_window_title(),
                                ] + arg_list
                                no_wait = True
                                open_in_terminal = True

                            elif (
                                term_emulator == "alacritty"
                                and is_alacritty_installed()
                            ):
                                arg_list = wrap_args_alacritty(
                                    arg_list,
                                    title=self.get_window_title(),
                                )
                                no_wait = True
                                open_in_terminal = True

                            elif SUPPORT_GNU_SCREEN and shutil.which("screen"):
                                arg_list = [
                                    "screen",
                                    "-S",
                                    slugify(self.get_window_title()),
                                ] + arg_list

                            else:
                                raise FileNotFoundError(
                                    "No terminal is available for `newWindow` on linux."
                                )

                        else:
                            new_window = False
                            no_wait = False

                    elif sys.platform == "darwin":
                        if is_alacritty_installed():
                            arg_list = wrap_args_alacritty(
                                arg_list,
                                title=self.get_window_title(),
                            )
                            no_wait = True
                            open_in_terminal = True
                        else:
                            arg_list = [
                                "osascript",
                                "-e",
                                'tell app "Terminal" to do script "%s"'
                                % _args_to_str(arg_list, shell_type="bash"),
                                "-e",
                                'tell app "Terminal" to activate',
                            ]

                    else:
                        logging.warning(
                            '"new_window" is not implemented on platform "%s"'
                            % sys.platform
                        )

                except FileNotFoundError as ex:
                    new_window = False
                    no_wait = False
                    logging.warning(ex)

            # Spawn a new process to run commands
            if no_wait:
                if sys.platform == "linux":
                    popen_extra_args["start_new_session"] = True

            if sys.platform == "win32" and use_shell_execute_win32:
                SW_SHOWNORMAL = 1
                lpParameters = _args_to_str(arg_list[1:], shell_type="cmd")
                logging.debug(
                    f"ShellExecuteW(): lpFile={arg_list[0]} lpParameters={lpParameters}"
                )
                ret = ctypes.windll.shell32.ShellExecuteW(
                    None,  # hwnd
                    None,  # lpOperation
                    arg_list[0],
                    lpParameters,
                    cwd,
                    SW_SHOWNORMAL,
                )
                success = ret > 32
                return success

            elif self.cfg["runAsAdmin"]:
                # Passing environmental variables
                args2 = wrap_args_cmd(
                    arg_list,
                    cwd=cwd,
                    title=self.get_window_title(),
                    env=env,
                )
                logging.debug("run_elevated(): args=%s" % args2)
                return_code = run_elevated(
                    args2, wait=not no_wait, show_terminal_window=not open_in_terminal
                )
                if no_wait:
                    return True
                else:
                    return return_code == 0

            else:
                logging.debug("cmdline: %s" % arg_list)
                logging.debug("popen_extra_args: %s" % popen_extra_args)
                logging.debug("env = %s" % env)
                self.ps = subprocess.Popen(
                    args=arg_list,
                    env={**os.environ, **env},
                    cwd=cwd,
                    shell=shell,
                    **popen_extra_args,
                )

                success = True
                if not no_wait:
                    with IgnoreSigInt():
                        success = self.ps.wait() == 0

                if background or out_to_file:
                    if BG_PROCESS_OUTPUT_TYPE == BackgroundProcessOutputType.LOG_PIPE:
                        LogPipe(self.ps.stdout, log_level=logging.INFO)
                        LogPipe(self.ps.stderr, log_level=logging.INFO)
                    elif (
                        BG_PROCESS_OUTPUT_TYPE
                        == BackgroundProcessOutputType.REDIRECT_TO_FILE
                    ):
                        # Close fd immediately. If we don't call `close()` the
                        # file handles will remain open in the parent process,
                        # which can cause potential issues like having many open
                        # file descriptors.
                        fd.close()

                return success

        else:  # no args
            return True

    def get_variable_names(self) -> List[str]:
        VARIABLE_NAME_PATT = r"\b([A-Z_$][A-Z_$0-9]{4,})\b"
        if self.cfg["variableNames"] == "auto":
            if self.ext in SCRIPT_EXTENSIONS:
                with open(self.script_path, "r", encoding="utf-8") as f:
                    s = f.read()

                    # Find all uppercase names to use as variable names.
                    variable_names = re.findall(VARIABLE_NAME_PATT, s)
            else:
                return []
        else:
            variable_names = self.cfg["variableNames"].split()

        # Remove duplicates
        variable_names = list(set(variable_names))

        # Convert private variable to global namespace
        prefix = self.get_public_variable_prefix()
        variable_names = [
            prefix + v if v.startswith("_") else v for v in variable_names
        ]

        variable_names = [x for x in variable_names if x not in VARIABLE_NAME_EXCLUDE]

        # Sort the variable names
        variable_names = sorted(variable_names)

        return variable_names

    def update_script_access_time(self):
        config_file = _get_script_access_time_file()
        update_json(config_file, {self.script_path: time.time()})


def get_script_variables(script: Script) -> Dict[str, str]:
    all_variables = get_all_variables()
    script_variables: Dict[str, str] = {}
    for name in script.get_variable_names():
        if name in all_variables:
            script_variables[name] = all_variables[name]
        else:
            script_variables[name] = ""
    return script_variables


@timed
def find_script(patt: str) -> Optional[str]:
    if os.path.exists(patt):
        return os.path.abspath(patt)

    script_path = get_absolute_script_path(patt)
    if os.path.exists(script_path):
        return script_path

    # Fuzzy search
    logging.debug(f"fuzzy search by: {patt}")
    for d in get_script_directories():
        path = os.path.join(d.path, "**", patt)

        match = glob.glob(path, recursive=True)
        match = [
            f
            for f in match
            if not os.path.isdir(f) and os.path.splitext(f)[1] in SCRIPT_EXTENSIONS
        ]
        if len(match) == 1:
            return match[0]
        elif len(match) > 1:
            raise Exception("Found multiple scripts: %s" % str(match))

    return None


def start_script(
    file: Optional[str] = None,
    args=[],
    cd=True,
    command_wrapper: Optional[bool] = None,
    config_override=None,
    console_title=None,
    new_window=None,
    restart_instance=None,
    single_instance=None,
    tee=None,
    template=None,
    variables=None,
):
    start_time = time.time()

    if file is None:
        file, args = get_last_script_and_args()

    # Print command line arguments
    logging.info(
        "cmdline: %s"
        % _args_to_str(
            [file] + args, shell_type="cmd" if sys.platform == "win32" else "bash"
        )
    )

    script_path = find_script(file)
    if script_path is None:
        raise Exception('Cannot find script: "%s"' % file)

    script = Script(script_path)

    if console_title:
        script.console_title = console_title

    if template is not None:
        script.cfg["template"] = template

    if config_override:
        for k, v in config_override.items():
            script.cfg[k] = v

    # Set console window title (for windows only)
    if console_title and sys.platform == "win32":
        # Save previous title
        MAX_BUFFER = 260
        saved_title = (ctypes.c_char * MAX_BUFFER)()
        res = ctypes.windll.kernel32.GetConsoleTitleA(saved_title, MAX_BUFFER)
        win_title = console_title.encode(locale.getpreferredencoding())
        ctypes.windll.kernel32.SetConsoleTitleA(win_title)

    if variables:
        script.set_override_variables(variables)

    ret = script.execute(
        args=args,
        cd=cd,
        command_wrapper=command_wrapper,
        new_window=new_window,
        restart_instance=restart_instance,
        single_instance=single_instance,
        tee=tee,
    )
    if not ret:
        raise subprocess.CalledProcessError(returncode=ret, cmd=args)

    # Restore title
    if console_title and sys.platform == "win32":
        ctypes.windll.kernel32.SetConsoleTitleA(saved_title)

    end_time = time.time()
    logging.info(
        "%s finished in %s" % (file, format_time(end_time - start_time)),
    )


def run_script(
    file: Optional[str] = None,
    args=[],
    new_window=False,  # should not start a new window by default
    restart_instance=False,
    single_instance=False,
    cd=True,
    command_wrapper=False,
    tee=False,
    **kwargs,
):
    start_script(
        file,
        args,
        cd=cd,
        command_wrapper=command_wrapper,
        new_window=new_window,
        restart_instance=restart_instance,
        single_instance=single_instance,
        tee=tee,
        **kwargs,
    )


def get_default_script_config() -> Dict[str, Union[str, bool, None]]:
    return {
        "adk.jdk_version": "",
        "adk": False,
        "args.clipboard": False,
        "args.clipboardAsFile": False,
        "args.selectDir": False,
        "args.selectFiles": False,
        "args.selection": False,
        "args.selectionAsFile": False,
        "args.userInput": False,
        "env.userInput": "",
        "args": "",
        "autoRun": False,
        "background": False,
        "closeOnExit": True,
        "cmake.version": "",
        "cmake": False,
        "cmdline": "",
        "commandWrapper": True,
        "conda": "",
        "globalHotkey": "",
        "hotkey": "",
        "matchClipboard": "",
        "minimized": False,
        "msys2": False,
        "newWindow": True,
        "openWithScript": "",
        "packages.pip": "",
        "packages": "",
        "reloadScriptsAfterRun": False,
        "restartInstance": False,
        "runAsAdmin": False,
        "runAtStartup": False,
        "runEveryNSec": "",
        "runOverSsh": False,
        "runpy": True,
        "runRemotely": False,
        "singleInstance": True,
        "tee": False,
        "template": None,
        "template.readVarFromCsv": "",
        "terminal": "alacritty",
        "title": "",
        "updateSelectedScriptAccessTime": False,
        "variableNames": "auto",
        "venv.name": "",
        "webApp": False,
        "workingDir": "",
        "wsl": False,
        "wsl.distro": "",
    }


def _load_script_config_file(file: str) -> Dict[str, Union[str, bool, None]]:
    config = load_json(file)
    return config


def _save_script_config_file(data: Dict[str, Union[str, bool, None]], file: str):
    if len(data) == 0:
        if os.path.isfile(file):
            os.remove(file)
    else:
        save_json(file, data)


def get_script_folder_level_config(
    script_path: str,
) -> Optional[Dict[str, Union[str, bool, None]]]:
    config_file_path = get_default_script_config_path(script_path)
    if os.path.exists(config_file_path):
        return _load_script_config_file(config_file_path)
    else:
        return None


def load_script_config(script_path) -> Dict[str, Union[str, bool, None]]:
    # Load script default config.
    config = get_default_script_config()

    # Load script folder-level config.
    folder_level_config = get_script_folder_level_config(script_path)
    if folder_level_config is not None:
        config.update(folder_level_config)

    # Load the script-level config.
    script_config_file = get_script_config_file(script_path)
    if script_config_file:
        script_level_config = _load_script_config_file(script_config_file)
        if script_level_config is not None:
            config.update(script_level_config)

    if "matchClipboard" in config and config["matchClipboard"]:
        config["matchClipboard"] = render_template(
            config["matchClipboard"], file_locator=find_script
        )

    return config


def update_script_config(kvp, script_file):
    default_config = get_default_script_config()
    script_config_file = get_script_config_file_path(script_file)
    if not os.path.exists(script_config_file):
        data = {}
    else:
        data = _load_script_config_file(script_config_file)
        if data is None:
            data = {}

    data = {**default_config, **data, **kvp}
    data = {k: v for k, v in data.items() if default_config[k] != v}
    _save_script_config_file(data, script_config_file)


def create_script_link(script_file):
    script_dir = os.path.abspath(SCRIPT_ROOT + "/../scripts")
    link_file = os.path.splitext(os.path.basename(script_file))[0] + ".link"
    link_file = os.path.join(script_dir, link_file)
    with open(link_file, "w", encoding="utf-8") as f:
        f.write(script_file)
    logging.info("Link created: %s" % link_file)


def is_instance_running() -> bool:
    LOCK_PATH = os.path.join(tempfile.gettempdir(), "myscripts_lock")
    if sys.platform == "win32":
        try:
            if os.path.exists(LOCK_PATH):
                os.unlink(LOCK_PATH)
            fh = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        except EnvironmentError as err:
            if err.errno == 13:
                return True
            else:
                raise
    else:
        import fcntl

        fh = os.open(LOCK_PATH, os.O_WRONLY | os.O_CREAT)
        try:
            fcntl.lockf(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return False
        except IOError:
            return True

    return False


def _get_script_access_time_file() -> str:
    return os.path.join(get_data_dir(), "script_access_time.json")


_script_access_time_file_mtime = 0.0
_cached_script_access_time: Dict[str, float] = {}


def get_all_script_access_time() -> Dict[str, float]:
    global _script_access_time_file_mtime
    global _cached_script_access_time

    config_file = _get_script_access_time_file()
    if not os.path.exists(config_file):
        return {}

    mtime = os.path.getmtime(config_file)
    if mtime > _script_access_time_file_mtime:
        _script_access_time_file_mtime = mtime
        with open(config_file, "r", encoding="utf-8") as f:
            _cached_script_access_time = json.load(f)

    return _cached_script_access_time


script_dir_config_file = ".scriptdirconfig.json"


def get_default_script_dir_config():
    return {"includeExts": ""}


def _get_scripts_recursive(
    directory: ScriptDirectory, include_exts=[]
) -> Iterator[str]:
    dir_config = load_json(
        os.path.join(directory.path, script_dir_config_file),
        default=get_default_script_dir_config(),
    )
    include_exts += dir_config["includeExts"].split()

    def should_ignore(dir: str, file: str):
        if (
            file == "tmp"
            or file == "generated"
            or file == ".config"
            or file == ".venv"
            or file == "node_modules"
        ):
            return True

        # Ignore folder starting with `_`
        if file.startswith("_"):
            return True

        # Ignore folder if `<folder>.ignore` exists
        if os.path.exists(os.path.join(dir, file + ".ignore")):
            return True

        return False

    for root, dirs, files in os.walk(directory.path, topdown=True):
        dirs[:] = [d for d in dirs if not should_ignore(root, d)]

        for file in files:
            ext = os.path.splitext(file)[1].lower()

            if directory.glob:
                if not fnmatch(file, directory.glob):
                    continue
            else:
                # Filter by script extensions
                if (
                    ext not in SCRIPT_EXTENSIONS
                    and ext not in include_exts
                    and ext not in BINARY_EXTENSIONS
                    and not file.endswith(".excalidraw.png")
                ):
                    continue

            yield os.path.join(root, file)


def get_all_scripts() -> Iterator[str]:
    for d in get_script_directories():
        files = _get_scripts_recursive(d)
        for file in files:
            # File has been removed during iteration
            if not os.path.exists(file):
                continue

            # Hide files starting with '_'
            base_name = os.path.basename(file)
            if base_name.startswith("_"):
                continue

            yield file


def execute_script_autorun(script: Script):
    assert script.cfg["autoRun"] or script.cfg["runAtStartup"]
    try:
        logging.debug("autorun: %s" % script.name)
        script.execute(command_wrapper=False)
    except Exception as ex:
        logging.warning(f"Failed to autorun script: {script.script_path}")
        logging.exception(ex)


def try_reload_scripts_autorun(scripts_autorun: List[Script]):
    for script in scripts_autorun:
        assert script.cfg["autoRun"]
        reloaded = script.refresh_script()
        if reloaded:
            execute_script_autorun(script)


def render_script(script_path) -> str:
    script = Script(script_path)
    return script.render()


def _load_dotenv(dotenv):
    load_dotenv(
        os.path.join(get_my_script_root(), "settings", "myscripts", "default_env.txt"),
        env=dotenv,
    )
    dot_env_file = os.path.join(get_data_dir(), ".env")
    if os.path.exists(dot_env_file):
        load_dotenv(
            dot_env_file,
            env=dotenv,
        )
