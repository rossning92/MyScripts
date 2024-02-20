import ctypes
import glob
import json
import locale
import logging
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from enum import IntEnum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

import yaml
from _android import setup_android_env
from _cpp import setup_cmake
from _editor import open_code_editor
from _filelock import FileLock
from _pkgmanager import require_package
from _shutil import (
    CONEMU_INSTALL_DIR,
    IgnoreSigInt,
    activate_window_by_name,
    close_window_by_name,
    convert_to_unix_path,
    format_time,
    get_ahk_exe,
    get_home_path,
    get_hotkey_abbr,
    load_json,
    load_yaml,
    npm_install,
    prepend_to_path,
    print2,
    quote_arg,
    run_elevated,
    save_json,
    save_yaml,
    setup_nodejs,
    shell_open,
    slugify,
    start_process,
    update_json,
    wrap_args_conemu,
    write_temp_file,
)
from _template import render_template
from utils.clip import get_clip, get_selection
from utils.term.alacritty import is_alacritty_installed, wrap_args_alacritty
from utils.timed import timed
from utils.tmux import is_in_tmux
from utils.venv import activate_python_venv, get_venv_python_executable

SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))

SCRIPT_EXTENSIONS = {
    ".ahk",
    ".bat",
    ".c",
    ".cc",
    ".cmd",
    ".cpp",
    ".expect",
    ".ipynb",  # Python
    ".js",
    ".link",
    ".md",
    ".mmd",  # mermaid source file
    ".ps1",
    ".py",
    ".sh",
    ".txt",
    ".url",
    ".vbs",  # Windows specific,
}

DEFAULT_TERMINAL_FONT_SIZE = 8
if sys.platform == "win32":
    WINDOWS_TERMINAL_EXEC = (
        os.environ["LOCALAPPDATA"] + "\\Microsoft\\WindowsApps\\wt.exe"
    )

VARIABLE_NAME_EXCLUDE = {"HOME", "PATH"}


class BackgroundProcessOutputType(IntEnum):
    LOG_PIPE = 1
    REDIRECT_TO_FILE = 2


background_process_output_type = BackgroundProcessOutputType.REDIRECT_TO_FILE


SUPPORT_GNU_SCREEN = False

DEFAULT_LINUX_TERMINAL = "alacritty"


@lru_cache(maxsize=None)
def get_script_root() -> str:
    # Reversely enumerate the script directories in case the user overrides the
    # default script directory root.
    for d in reversed(get_script_directories()):
        if d.name == "":
            logging.debug(f"Script root: {d.path}")
            return d.path

    raise Exception("Failed to find script root directory.")


@lru_cache(maxsize=None)
def get_my_script_root():
    return os.path.abspath(SCRIPT_ROOT + "/../")


@lru_cache(maxsize=None)
def get_data_dir() -> str:
    data_dir_config_file = os.path.abspath(
        os.path.join(SCRIPT_ROOT, "..", "config", "data_dir.txt")
    )
    if os.path.exists(data_dir_config_file):
        with open(data_dir_config_file, "r") as f:
            data_dir = f.read().strip()
            if not os.path.isabs(data_dir):  # if relative path
                data_dir = os.path.normpath(
                    os.path.join(
                        get_my_script_root(), data_dir.replace("/", os.path.sep)
                    )
                )

    else:
        data_dir = os.path.abspath("%s/../tmp/data/%s" % (SCRIPT_ROOT, platform.node()))
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def setup_env_var(env):
    root = get_my_script_root()

    bin_dir = os.path.join(root, "bin")
    prepend_to_path(bin_dir, env=env)

    env["PYTHONPATH"] = os.path.join(root, "libs")
    env["MY_DATA_DIR"] = get_data_dir()
    env["MY_TEMP_DIR"] = get_temp_dir()


def get_bin_dir():
    return os.path.abspath(SCRIPT_ROOT + "/../bin")


@lru_cache(maxsize=None)
def get_script_dirs_config_file():
    config_json_file = os.path.join(get_data_dir(), "script_directories.json")
    return config_json_file


@dataclass
class ScriptDirectory:
    name: str
    path: str  # absolute path of script directory


@lru_cache(maxsize=None)
def get_script_directories() -> List[ScriptDirectory]:
    directories: List[ScriptDirectory] = []

    # Default script root path
    directories.append(
        ScriptDirectory(name="", path=os.path.join(get_my_script_root(), "scripts"))
    )

    config_file = get_script_dirs_config_file()
    data = load_json(config_file, default=[])

    for item in data:
        name = item["name"]

        directory = item["directory"]
        if not os.path.isabs(directory):  # is relative path
            directory = os.path.abspath(
                os.path.join(
                    # Relative to "script_directories.json" config file
                    os.path.dirname(config_file),
                    directory,
                )
            )

        directories.append(ScriptDirectory(name=name, path=directory))

    return directories


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


def get_script_history_file():
    return os.path.join(os.path.join(get_data_dir(), "last_script.json"))


def get_last_script_and_args() -> Tuple[str, Any]:
    if os.path.exists(get_script_history_file()):
        with open(get_script_history_file(), "r") as f:
            data = json.load(f)
            return data["file"], data["args"]
    else:
        raise ValueError("file cannot be None.")


def wrap_wsl(
    commands: Union[List[str], Tuple[str], str], env: Dict[str, str]
) -> List[str]:
    if not os.path.exists(r"C:\Windows\System32\bash.exe"):
        raise Exception("WSL (Windows Subsystem for Linux) is not installed.")
    logging.debug("wrap_wsl(): cmd: %s" % commands)

    # To create a temp bash script to invoke commands to avoid command being parsed
    # by current shell
    bash = ""

    # Workaround: PATH environmental variable can't be shared between windows
    # and linux (WSL)
    if "PATH" in env:
        del env["PATH"]

    if env is not None:
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
    return [
        "bash.exe",
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
    args: List[str], wsl=False, env: Optional[Dict[str, str]] = None, msys2=False
) -> List[str]:
    if sys.platform == "win32":
        if wsl:  # WSL (Windows Subsystem for Linux)
            return wrap_wsl(args, env=env)

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
    if shell_type == "powershell":
        return " ".join(
            [x.replace(" ", "` ").replace("(", "`(").replace(")", "`)") for x in args]
        )
    else:
        return " ".join([quote_arg(x, shell_type=shell_type) for x in args])


@lru_cache(maxsize=None)
def get_variable_edit_history_file():
    return os.path.join(get_data_dir(), "variable_edit_history.json")


@lru_cache(maxsize=None)
def get_variable_file():
    variable_file_v2 = os.path.join(get_data_dir(), "variables_v2.json")

    # TODO: migrate to new variable file
    if True:
        if not os.path.exists(variable_file_v2):
            variable_file_v1 = os.path.join(get_data_dir(), "variables.json")
            if os.path.exists(variable_file_v1):
                shutil.copy(variable_file_v1, get_variable_edit_history_file())

                variables = load_json(variable_file_v1)
                variables_v2 = {k: v[0] for k, v in variables.items()}
                save_json(variable_file_v2, variables_v2)

    return variable_file_v2


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


def read_setting(setting, name, val):
    file = os.path.join(get_data_dir(), "%s.json" % setting)

    try:
        with open(file, "r") as f:
            data = json.load(f)
    except IOError:
        return

    if name not in data:
        return

    return data[name]


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


def input2(message, name):
    val = get_variable(name)
    user_input = input("%s (default: %s): " % (message, val))
    if not user_input and val:
        return val

    set_variable(name, val)
    return user_input


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
    font_size=None,
    default_font_size=DEFAULT_TERMINAL_FONT_SIZE,
    icon=None,
    opacity=1.0,
    **kwargs,
) -> List[str]:
    if sys.platform != "win32":
        raise Exception("OS not supported.")

    # Escape simicolons used in wt command.
    args = [x.replace(";", r"\;") for x in args]

    CONFIG_FILE = os.path.expandvars(
        r"%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"
    )

    with open(CONFIG_FILE, "r") as f:
        lines = f.read().splitlines()

    lines = [x for x in lines if not x.lstrip().startswith("//")]
    data = json.loads("\n".join(lines))

    updated = False

    settings = {
        "initialCols": 120,
        "initialRows": 40,
    }
    for k, v in settings.items():
        if k not in data or data[k] != v:
            data[k] = v
            updated = True

    # Default font size and color scheme
    profiles_defaults = {
        "colorScheme": "One Half Dark",
        "font": {"face": "Consolas", "size": default_font_size},
    }
    if profiles_defaults != data["profiles"]["defaults"]:
        data["profiles"]["defaults"] = profiles_defaults
        updated = True

    # Customize selection color
    for scheme in filter(lambda x: x["name"] == "One Half Dark", data["schemes"]):
        if scheme["selectionBackground"] != "#ffff00":
            scheme["selectionBackground"] = "#ffff00"
            updated = True

    if title:
        filtered = list(filter(lambda x: x["name"] == title, data["profiles"]["list"]))
        profile = {
            "name": title,
            "hidden": False,
            "suppressApplicationTitle": True,
        }
        if font_size is not None:
            profile["fontSize"] = font_size

        if opacity < 1:
            profile["useAcrylic"] = True
            profile["acrylicOpacity"] = opacity

        if icon is not None:
            profile["icon"] = icon.replace("\\", "/")

        if len(filtered) == 0:
            data["profiles"]["list"].append(profile)
            updated = True
        elif profile != filtered[0]:
            filtered[0].update(profile)
            updated = True

        if updated:
            # Only update when config file is changed
            with open(CONFIG_FILE, "w") as f:
                json.dump(data, f, indent=4)

        return [WINDOWS_TERMINAL_EXEC, "-p", title] + args
    else:
        return [WINDOWS_TERMINAL_EXEC] + args


def get_relative_script_path(path: str) -> str:
    path = path.replace("\\", "/")
    for d in get_script_directories():
        prefix = d.path.replace("\\", "/") + "/"
        if path.startswith(prefix):
            path = (d.name + "/" if d.name else "") + path[len(prefix) :]
            break
    return path


def get_absolute_script_path(path: str):
    # If already absolute path
    if os.path.isabs(path):
        return path

    script_dirs = get_script_directories()
    path_arr = path.split("/")
    if path_arr:
        if path_arr[0] == "r" or path_arr[0] == "ext":
            path_arr.insert(0, os.path.join(get_my_script_root(), "scripts"))
        else:
            matched_script_dir = next(
                filter(lambda d: d.name == path_arr[0], script_dirs), None
            )
            if matched_script_dir:
                path_arr[0] = matched_script_dir.path
            else:
                path_arr.insert(0, get_script_root())
    return os.path.join(*path_arr)


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


class Script:
    def __init__(self, script_path: str, name=None):
        if not os.path.isfile(script_path):
            raise Exception("Script file does not exist.")

        script_path = os.path.abspath(script_path)
        self.script_rel_path = get_relative_script_path(script_path)

        # Script display name
        if name:
            self.name = name
        else:
            self.name = self.script_rel_path

        self.ext = os.path.splitext(script_path)[1].lower()  # Extension / script type
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

    def match_pattern(self, text: str):
        patt = self.cfg["matchClipboard"]
        return patt and re.search(patt, text) is not None

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
        if self.cfg["hotkey"]:
            s += " (%s)" % (get_hotkey_abbr(self.cfg["hotkey"]))
        if self.cfg["globalHotkey"]:
            s += " {%s}" % (get_hotkey_abbr(self.cfg["globalHotkey"]))
        if self.cfg["autoRun"]:
            s += " [autorun]"

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

    def get_window_title(self):
        if self.console_title:
            return self.console_title
        elif self.cfg["title"]:
            return self.cfg["title"]
        else:
            return self.name

    def get_script_path(self) -> str:
        return self.real_script_path if self.real_script_path else self.script_path

    def get_script_source(self) -> str:
        if self.ext in [".bat", ".cmd"]:
            encoding = locale.getpreferredencoding()
        else:
            encoding = "utf-8"

        script_path = self.get_script_path()
        with open(script_path, "r", encoding=encoding) as f:
            source = f.read()

        return source

    def render(self, source: Optional[str] = None, variables=None) -> str:
        if variables is None:
            variables = self.get_variables()

        if not self.check_link_existence():
            raise Exception("Link is invalid.")

        if source is None:
            source = self.get_script_source()

        cwd = os.getcwd()
        script_path = self.get_script_path()
        script_dir = os.path.dirname(script_path)
        if script_dir:
            os.chdir(script_dir)

        result = render_template(source, variables, file_locator=find_script)

        os.chdir(cwd)
        return result

    def set_override_variables(self, variables):
        self.override_variables = variables

    def get_variables(self) -> Dict[str, str]:
        vnames = self.get_variable_names()
        saved_variables = get_all_variables()

        # Get all variables
        variables = {}
        for vname in vnames:
            if vname in saved_variables:
                last_modified_value = saved_variables[vname]
                # Note that last_modified_value can be an empty string
                variables[vname] = last_modified_value
            else:
                variables[vname] = ""

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
        return {"HOME": get_home_path(), "SCRIPT": quote_arg(self.script_path)}

    def activate_window(self) -> bool:
        title = self.get_window_title()
        if (
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
        command_wrapper: Optional[bool] = True,
        background=False,
    ) -> bool:
        # Termux does not have any GUI support, so we never open script in new window.
        # if is_in_termux():
        #     new_window = False

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

        new_window = self.cfg["newWindow"] if new_window is None else new_window
        # TODO: Mac does not support newWindow yet
        if sys.platform == "darwin":
            new_window = False

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

        logging.info(
            "execute: %s %s"
            % (self.name, _args_to_str(args, shell_type="bash") if args else "")
        )

        close_on_exit = (
            close_on_exit if close_on_exit is not None else self.cfg["closeOnExit"]
        )
        logging.debug(f"close_on_exit={close_on_exit}")

        if ext == ".md" or ext == ".txt":
            open_code_editor(script_path)
            return True

        arg_list = args

        # If no arguments is provided to the script, try to provide the default
        # values from the script config.
        if len(arg_list) == 0:
            if self.cfg["args"]:
                arg_list += self.cfg["args"].split()

            if self.cfg["args.passSelectionAsFile"]:
                selection = get_selection()
                temp_file = write_temp_file(selection, ".txt")
                arg_list.append(temp_file)

            elif self.cfg["args.passUserInput"]:
                from utils.menu.input import Input

                text = Input().input()
                if not text:
                    return True
                arg_list.append(text)

            elif self.cfg["args.passSelection"]:
                selection = get_selection()
                arg_list.append(selection)

            elif self.cfg["args.passClipboard"]:
                clipboard = get_clip()
                arg_list.append(clipboard)

            elif self.cfg["args.passClipboardAsFile"]:
                clipboard = get_clip()
                temp_file = write_temp_file(clipboard, ".txt")
                arg_list.append(temp_file)

            elif self.cfg["args.passSelectedFile"]:
                from utils.menu.filemgr import FileManager

                file = FileManager().select_file()
                if file is None:
                    return True
                else:
                    arg_list.append(file)

            elif self.cfg["args.passSelectedDir"]:
                from utils.menu.filemgr import FileManager

                file = FileManager().select_directory()
                if file is None:
                    return True
                else:
                    arg_list.append(file)

        # Override environmental variables with `variables`
        env = {**variables}

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
            source = self.get_script_source()
            template = "{{" in source
        else:
            source = None
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

        if cd:
            if self.cfg["workingDir"]:
                cwd = self.cfg["workingDir"].format(**self.get_context())
                if not os.path.exists(cwd):
                    os.makedirs(cwd, exist_ok=True)
            else:
                cwd = os.path.abspath(
                    os.path.join(os.getcwd(), os.path.dirname(script_path))
                )
        else:
            cwd = None

        if "CWD" in os.environ:
            cwd = os.environ["CWD"]
        logging.debug("CWD = %s" % cwd)

        # Automatically convert path arguments to UNIX path if running in WSL
        if sys.platform == "win32" and self.cfg["wsl"]:
            arg_list = [convert_to_unix_path(x, wsl=self.cfg["wsl"]) for x in arg_list]

        cmdline = self.cfg["cmdline"]
        if cmdline:
            arg_list = shlex.split(cmdline.format(**self.get_context()))

        elif ext == ".ps1":
            if sys.platform == "win32":
                if template:
                    ps_path = write_temp_file(
                        self.render(source=source), slugify(self.name) + ".ps1"
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
                        self.render(source=source),
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
                        self.render(source=source), slugify(self.name) + ".cmd"
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
                        f.write(self.render(source=source))

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
                    self.render(source=source), slugify(self.name) + ".sh"
                )
            script_path = convert_to_unix_path(script_path, wsl=self.cfg["wsl"])

            arg_list = [script_path] + arg_list
            arg_list = wrap_bash_commands(
                arg_list, wsl=self.cfg["wsl"], env=env, msys2=self.cfg["msys2"]
            )

        elif ext == ".expect":
            arg_list = wrap_bash_commands(
                ["expect", convert_to_unix_path(script_path, wsl=True)],
                wsl=True,
                env=env,
            )

        elif ext == ".py" or ext == ".ipynb":
            if self.cfg["venv.name"]:
                python_exec = get_venv_python_executable(self.cfg["venv.name"])
            else:
                python_exec = sys.executable

            if template and ext == ".py":
                python_file = write_temp_file(
                    self.render(source=source), slugify(self.name) + ".py"
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
            if self.cfg["packages.pip"]:
                pip_packages = self.cfg["packages.pip"].split()
                for pkg in pip_packages:
                    # Check if pip package is installed
                    ret = subprocess.call(
                        [python_exec, "-m", "pip", "show", pkg],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    if ret != 0:
                        print(f"{pkg} is not found, installing...")
                        subprocess.check_call(
                            [python_exec, "-m", "pip", "install", pkg]
                        )

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

        elif ext == ".url":
            url = self.get_script_source()
            if "%s" in url:
                from utils.menu.input import Input

                if len(arg_list) == 1:
                    keyword = arg_list[0]
                else:
                    keyword = Input().input()
                    if not keyword:
                        return True
                url = url.replace("%s", keyword)

            fallback_to_shell_open = True
            if self.cfg["webApp"]:
                chrome_executables = ["google-chrome-stable", "google-chrome", "chrome"]
                if sys.platform == "win32":
                    chrome_executables.insert(
                        0, r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                    )
                for chrome_exec in chrome_executables:
                    if shutil.which(chrome_exec):
                        # args = [chrome_exec, "--new-window"]
                        # if self.cfg["title"]:
                        #     args.append(f"--window-name={self.cfg['title']}")
                        # args.append(url)
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
                log_file = os.path.join(
                    get_home_path(),
                    "Desktop",
                    "{}_{}.log".format(self.get_short_name(), int(time.time())),
                )
                # arg_list = wrap_args_tee(
                #     arg_list,
                #     out_file=log_file,
                # )
                # open_log_file(log_file)
                arg_list = [
                    sys.executable,
                    os.path.join(get_my_script_root(), "scripts", "r", "logviewer.py"),
                    log_file,
                    "--cmdline",
                ] + arg_list

            no_wait = False
            open_in_terminal = False
            popen_extra_args: Dict[str, Any] = {}

            if command_wrapper is None:
                command_wrapper = self.cfg["commandWrapper"]
            logging.debug(f"command_wrapper={command_wrapper}")

            if command_wrapper and not background and not self.cfg["minimized"]:
                # Add command wrapper to pause on exit
                env["CLOSE_ON_EXIT"] = "1" if close_on_exit else "0"
                arg_list = [
                    sys.executable,
                    os.path.join(get_bin_dir(), "command_wrapper.py"),
                ] + arg_list

            if background:
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

                if (
                    background_process_output_type
                    == BackgroundProcessOutputType.LOG_PIPE
                ):
                    popen_extra_args["stdin"] = subprocess.DEVNULL
                    popen_extra_args["stdout"] = subprocess.PIPE
                    popen_extra_args["stderr"] = subprocess.PIPE

                elif (
                    background_process_output_type
                    == BackgroundProcessOutputType.REDIRECT_TO_FILE
                ):
                    fd = open(self.get_script_log_file(), "w")
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

                            # Workaround that prevents alacritty from being
                            # closed by parent terminal. The "shell = True"
                            # below is very important!
                            DETACHED_PROCESS = 0x00000008
                            # CREATE_BREAKAWAY_FROM_JOB = 0x01000000
                            popen_extra_args["creationflags"] = (
                                subprocess.CREATE_NEW_PROCESS_GROUP
                                | DETACHED_PROCESS
                                # | CREATE_BREAKAWAY_FROM_JOB
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

                    elif sys.platform == "linux":
                        if is_in_tmux():
                            arg_list = (
                                [
                                    "tmux",
                                    # "split-window",
                                    "new-window",
                                    "-n",
                                    slugify(self.get_window_title()),
                                ]
                                + [  # Pass environmental variable to new window.
                                    item
                                    for k, v in env.items()
                                    for item in ("-e", f"{k}={v}")
                                ]
                                + arg_list
                            )

                        elif os.environ.get("DISPLAY"):
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

                if background:
                    if (
                        background_process_output_type
                        == BackgroundProcessOutputType.LOG_PIPE
                    ):
                        LogPipe(self.ps.stdout, log_level=logging.INFO)
                        LogPipe(self.ps.stderr, log_level=logging.INFO)
                    elif (
                        background_process_output_type
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
        VARIABLE_NAME_PATT = r"\b([A-Z_$][A-Z_$0-9]{5,})\b"
        if self.cfg["variableNames"] == "auto":
            if self.ext in SCRIPT_EXTENSIONS:
                with open(self.script_path, "r", encoding="utf-8") as f:
                    s = f.read()

                    # Search all environmental variable names using regular expressions.
                    # For example: "env: ENV_VAR_NAME".
                    variable_names = re.findall("env: " + VARIABLE_NAME_PATT, s)

                    # Fallback to matching all uppercase names.
                    if len(variable_names) == 0:
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
        raise Exception(f"{file} returned non-zero exit status {ret}")

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
    tee=False,
    **kwargs,
):
    start_script(
        file,
        args,
        cd=cd,
        command_wrapper=False,
        new_window=new_window,
        restart_instance=restart_instance,
        single_instance=single_instance,
        tee=tee,
        **kwargs,
    )


def get_default_script_config() -> Dict[str, Any]:
    return {
        "adk.jdk_version": "",
        "adk": False,
        "args.passClipboard": False,
        "args.passClipboardAsFile": False,
        "args.passSelectedDir": False,
        "args.passSelectedFile": False,
        "args.passSelection": False,
        "args.passSelectionAsFile": False,
        "args.passUserInput": False,
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
        "packages.pip": "",
        "packages": "",
        "reloadScriptsAfterRun": False,
        "restartInstance": False,
        "runAsAdmin": False,
        "runAtStartup": False,
        "runEveryNSec": "",
        "runpy": True,
        "singleInstance": True,
        "tee": False,
        "template": None,
        "terminal": "alacritty",
        "title": "",
        "updateSelectedScriptAccessTime": False,
        "variableNames": "auto",
        "venv.name": "",
        "webApp": False,
        "workingDir": "",
        "wsl": False,
    }


def get_script_config_file_path(script_path: str) -> str:
    return os.path.splitext(script_path)[0] + ".config.yaml"


def get_default_script_config_path(script_path: str) -> str:
    return os.path.join(os.path.dirname(script_path), "default.config.yaml")


def get_script_folder_level_config(script_path: str) -> Optional[Dict[str, Any]]:
    config_file_path = get_default_script_config_path(script_path)
    if os.path.exists(config_file_path):
        with open(config_file_path, "r") as f:
            return yaml.load(f.read(), Loader=yaml.FullLoader)
    else:
        return None


def get_script_config_file(script_path: str) -> Optional[str]:
    f = get_script_config_file_path(script_path)
    if os.path.exists(f):
        return f

    return None


def load_script_config(script_path) -> Dict[str, Any]:
    # Load script default config.
    config = get_default_script_config()

    # Load script folder-level config.
    folder_level_config = get_script_folder_level_config(script_path)
    if folder_level_config is not None:
        config.update(folder_level_config)

    # Load the script-level config.
    script_config_file = get_script_config_file(script_path)
    if script_config_file:
        with open(script_config_file, "r") as f:
            script_level_config = yaml.load(f.read(), Loader=yaml.FullLoader)
        if script_level_config is not None:
            config.update(script_level_config)

    return config


def update_script_config(kvp, script_file):
    default_config = get_default_script_config()
    script_config_file = get_script_config_file_path(script_file)
    if not os.path.exists(script_config_file):
        data = {}
    else:
        data = load_yaml(script_config_file)
        if data is None:
            data = {}

    data = {**default_config, **data, **kvp}
    data = {k: v for k, v in data.items() if default_config[k] != v}
    save_yaml(data, script_config_file)


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
        with open(config_file, "r") as f:
            _cached_script_access_time = json.load(f)

    return _cached_script_access_time


script_dir_config_file = ".scriptdirconfig.json"


def get_default_script_dir_config():
    return {"includeExts": ""}


def get_scripts_recursive(directory, include_exts=[]) -> Iterator[str]:
    dir_config = load_json(
        os.path.join(directory, script_dir_config_file),
        default=get_default_script_dir_config(),
    )
    include_exts += dir_config["includeExts"].split()

    def should_ignore(dir, file):
        if (
            file == "tmp"
            or file == "generated"
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

    for root, dirs, files in os.walk(directory, topdown=True):
        dirs[:] = [d for d in dirs if not should_ignore(root, d)]

        for file in files:
            ext = os.path.splitext(file)[1].lower()

            # Filter by script extensions
            if ext not in SCRIPT_EXTENSIONS and ext not in include_exts:
                continue

            yield os.path.join(root, file)


def get_all_scripts() -> Iterator[str]:
    for d in get_script_directories():
        files = get_scripts_recursive(d.path)
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


@lru_cache(maxsize=None)
def get_temp_dir() -> str:
    temp_dir = os.path.join(tempfile.gettempdir(), "MyScripts")
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir
