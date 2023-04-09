import bisect
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
import time
from functools import lru_cache
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Union

import yaml
from _android import setup_android_env
from _cpp import setup_cmake
from _editor import open_in_editor
from _filelock import FileLock
from _pkgmanager import open_log_file, require_package
from _shutil import (
    CONEMU_INSTALL_DIR,
    activate_window_by_name,
    call_echo,
    clear_env_var_explorer,
    close_window_by_name,
    convert_to_unix_path,
    file_is_old,
    format_time,
    get_ahk_exe,
    get_home_path,
    getch,
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
    wrap_args_conemu,
    write_temp_file,
)
from _template import render_template

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

RESERVED_VARIABLE_NAMES = {"HOME"}


def get_script_root():
    return os.path.abspath(SCRIPT_ROOT + "/../scripts")


def get_my_script_root():
    return os.path.abspath(SCRIPT_ROOT + "/../")


def is_in_wsl() -> bool:
    return "microsoft-standard" in platform.uname().release


@lru_cache(maxsize=None)
def get_data_dir():
    data_dir_file = os.path.abspath(
        os.path.join(SCRIPT_ROOT, "..", "config", "data_dir.txt")
    )
    if os.path.exists(data_dir_file):
        with open(data_dir_file, "r") as f:
            data_dir = f.read().strip()

            if is_in_wsl():
                data_dir = convert_to_unix_path(data_dir, wsl=True)

            if not os.path.isabs(data_dir):
                data_dir = os.path.join(
                    get_my_script_root(), data_dir.replace("/", os.path.sep)
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


def get_bin_dir():
    return os.path.abspath(SCRIPT_ROOT + "/../bin")


@lru_cache(maxsize=None)
def get_script_dirs_config_file():
    # TODO: migrate to json file
    config_txt_file_deprecated = os.path.join(get_data_dir(), "script_directories.txt")
    config_json_file = os.path.join(get_data_dir(), "script_directories.json")
    if os.path.exists(config_txt_file_deprecated):
        if not os.path.exists(config_json_file):
            with open(config_txt_file_deprecated) as f:
                lines = f.read().splitlines()

            directories = []
            for line in lines:
                line = line.strip()
                if line:
                    cols = line.split("|")
                    if len(cols) == 1:
                        name = os.path.basename(cols[0])
                        directory = cols[0]
                    elif len(cols) == 2:
                        name = cols[0]
                        directory = cols[1]
                    else:
                        raise Exception(
                            "Invalid line in {}: {}".format(
                                config_txt_file_deprecated, line
                            )
                        )
                directories.append({"name": name, "directory": directory})
            save_json(config_json_file, directories)
            os.rename(config_txt_file_deprecated, config_txt_file_deprecated + ".bak")

    if not os.path.exists(config_json_file):
        save_json(config_json_file, [])

    return config_json_file


@lru_cache(maxsize=None)
def get_script_directories() -> List[Tuple[str, str]]:
    directories = []
    directories.append(("", get_script_root()))

    config_file = get_script_dirs_config_file()
    data = load_json(config_file)

    for item in data:
        name = item["name"]
        directory = item["directory"]
        if not os.path.isabs(directory):  # is relative path
            directory = os.path.abspath(
                os.path.join(
                    # relative to "script_directories.txt"
                    os.path.dirname(config_file),
                    directory,
                )
            )
        directories.append((name, directory))

    return directories


def add_script_dir(d, prefix=None):
    if prefix is None:
        prefix = "link/" + os.path.basename(d)

    config_file = get_script_dirs_config_file()
    data = load_json(config_file)
    # Remove existing item given by name
    data = [item for item in data if item["name"] != prefix]
    # Add new item
    data.append({"name": prefix, "directory": d})
    save_json(config_file, data)


def _get_script_history_file():
    return os.path.join(os.path.join(get_data_dir(), "last_script.json"))


def get_last_script():
    if os.path.exists(_get_script_history_file()):
        with open(_get_script_history_file(), "r") as f:
            data = json.load(f)
            return data["file"]
    else:
        raise ValueError("file cannot be None.")


def wrap_wsl(commands, env=None):
    if not os.path.exists(r"C:\Windows\System32\bash.exe"):
        raise Exception("WSL (Windows Subsystem for Linux) is not installed.")
    logging.debug("wrap_wsl(): cmd: %s" % commands)

    # To create a temp bash script to invoke commands to avoid command being parsed
    # by current shell
    bash = ""

    # Workaround: PATH environmental variable can't be shared between windows and linux (WSL)
    if "PATH" in env:
        del env["PATH"]

    if env is not None:
        for k, v in env.items():
            bash += "export {}='{}'\n".format(k, v)

    if type(commands) in [list, tuple]:
        bash += _args_to_str(commands, shell_type="bash")
    else:
        bash += commands

    tmp_sh_file = write_temp_file(bash, ".sh")
    tmp_sh_file = convert_to_unix_path(tmp_sh_file, wsl=True)

    # # Escape dollar sign? Why?
    # commands = commands.replace("$", r"\$")
    # return ["bash.exe", "-c", commands]

    logging.debug("wrap_wsl(): write temp shell script: %s" % tmp_sh_file)
    return ["bash.exe", "-c", tmp_sh_file]


def wrap_bash_msys2(commands: str, env: Optional[Dict[str, str]] = None, msys2=False):
    if env is not None:
        # https://www.msys2.org/wiki/MSYS2-introduction/#path
        env["MSYS_NO_PATHCONV"] = "1"  # Disable path conversion
        env["CHERE_INVOKING"] = "1"  # stay in the current working directory
        env["MSYSTEM"] = "MINGW64"
        env["HOME"] = get_home_path()
        # Export full PATH environment variable into MSYS2
        env["MSYS2_PATH_TYPE"] = "inherit"

    tmp_sh_file = write_temp_file(commands, ".sh")

    msys2_bash_search_list = []
    if msys2:
        msys2_bash_search_list += [
            r"C:\tools\msys64\usr\bin\bash.exe",
            r"C:\msys64\usr\bin\bash.exe",
        ]
    msys2_bash_search_list += [
        r"C:\Program Files\Git\bin\bash.exe",
    ]
    bash = None
    for f in msys2_bash_search_list:
        if os.path.exists(f):
            bash = f
            break
    logging.debug("bash path: %s" % bash)

    if bash is None:
        raise Exception("Cannot find MinGW bash.exe")
    return [bash, "--login", "-i", tmp_sh_file]


def wrap_bash_commands(
    commands: str, wsl=False, env: Optional[Dict[str, str]] = None, msys2=False
):

    if sys.platform == "win32":
        if wsl:  # WSL (Windows Subsystem for Linux)
            return wrap_wsl(commands, env=env)

        else:
            return wrap_bash_msys2(commands, env=env, msys2=msys2)

    else:  # Linux
        tmp_sh_file = write_temp_file(commands, ".sh")
        return ["bash", "-i", tmp_sh_file]


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
def get_variable_file():
    variable_file = os.path.join(get_data_dir(), "variables.json")
    return variable_file


def get_all_variables() -> Dict[str, List]:
    file = get_variable_file()

    with FileLock("access_variable"):
        if not os.path.exists(file):
            return {}

        with open(file, "r", encoding="utf-8") as f:
            variables = json.load(f)
            return variables


def get_script_variables(script) -> Dict[str, List]:
    all_vars = get_all_variables()
    vars: Dict[str, List] = {}
    for var_name in script.get_variable_names():
        if var_name in all_vars:
            vars[var_name] = all_vars[var_name]
        else:
            vars[var_name] = []
    return vars


def get_variable(name):
    with FileLock("access_variable"):
        f = get_variable_file()
        if not os.path.exists(f):
            return

        with open(get_variable_file(), "r") as f:
            variables = json.load(f)

        if name not in variables:
            return

        return variables[name][0]


def set_variable(name, val):
    logging.info("Set %s=%s" % (name, val))
    assert val is not None

    with FileLock("access_variable"):
        file = get_variable_file()
        with open(file, "r", encoding="utf-8") as f:
            variables = json.load(f)

        if name not in variables:
            variables[name] = []
        vals = variables[name]

        try:
            vals.remove(val)
        except ValueError:
            pass

        vals.insert(0, val)

        with open(file, "w", encoding="utf-8") as f:
            json.dump(variables, f, indent=2)


def save_variables(variables):
    config_file = get_variable_file()
    with FileLock("access_variable"):
        if not os.path.exists(config_file):
            data = {}
        else:
            with open(get_variable_file(), "r") as f:
                data = json.load(f)

        data.update(variables)

        with open(config_file, "w") as f:
            json.dump(data, f, indent=4)


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

    script_root = get_script_root()
    python_path.append(os.path.join(script_root))
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
    assert type(args) is list

    if sys.platform == "win32":
        s = (
            "& "
            + _args_to_str(args, shell_type="powershell")
            + r" | Tee-Object -FilePath %s" % out_file
        )
        tmp_file = write_temp_file(s, ".ps1")
        logging.debug('wrap_args_tee(file="%s"): %s' % (tmp_file, s))
        return ["powershell", tmp_file]
    else:
        return args


def wrap_args_cmd(args, title=None, cwd=None, env=None) -> str:
    assert type(args) is list

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
):
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


def get_hotkey_abbr(hotkey):
    hotkey = (
        hotkey.lower().replace("win+", "#").replace("ctrl+", "^").replace("alt+", "!")
    )
    hotkey = re.sub(r"shift\+([a-z])", lambda m: m.group(1).upper(), hotkey)
    return hotkey


def wrap_args_alacritty(
    args,
    title=None,
    font_size=None,
    font=None,
    borderless=False,
    position=None,
    padding=None,
    **kwargs,
):
    assert isinstance(args, list)

    if not shutil.which("alacritty"):
        raise FileNotFoundError("Alacritty is not installed.")

    # https://github.com/alacritty/alacritty/blob/master/alacritty.yml
    if sys.platform == "windows":
        dest_path = os.path.expandvars(r"%APPDATA%\alacritty\alacritty.yml")
    else:
        dest_path = os.path.expanduser("~/.config/alacritty/alacritty.yml")
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    src_path = os.path.abspath(SCRIPT_ROOT + "/../settings/alacritty.yml")
    if file_is_old(src_path, dest_path):
        shutil.copy(src_path, dest_path)

    out = ["alacritty"]

    # Override configuration file options
    options = []
    if font_size is not None:
        out += [
            f"font.size={font_size}",
        ]
    if font is not None:
        options += [f"font.normal.family={font}"]
    if borderless:
        options += ["window.decorations=none"]
    if position:
        options += [
            f"window.position.x={position[0]}",
            f"window.position.y={position[1]}",
        ]
    if padding is not None:
        options += [f"window.padding.x={padding}", f"window.padding.y={padding}"]

    if len(options) > 0:
        out += ["-o"] + options

    if title:
        out += ["--title", title]

    # HACK: Alacritty handles spaces in a weird way: if arg has space in it, must double quote it.
    if sys.platform == "win32":
        args = [f'"{x}"' if " " in x else x for x in args]
    out += ["-e"] + args
    return out


def get_relative_script_path(path):
    path = path.replace("\\", "/")
    for name, d in get_script_directories():
        prefix = d.replace("\\", "/") + "/"
        if path.startswith(prefix):
            path = (name + "/" if name else "") + path[len(prefix) :]
            break
    return path


def get_absolute_script_path(path):
    # If already absolute path
    if os.path.isabs(path):
        return path

    script_dirs = get_script_directories()
    arr = path.split("/")
    if arr:
        matched_script_dir = next(filter(lambda x: x[0] == arr[0], script_dirs), None)
        if matched_script_dir:
            arr[0] = matched_script_dir[1]
        else:
            arr = [get_script_root()] + arr
    path = os.path.join(*arr)
    return path


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

            # Strip extension
            # self.name, _ = os.path.splitext(self.name)

        self.ext = os.path.splitext(script_path)[1].lower()  # Extension / script type
        self.override_variables = None
        self.console_title = None
        self.script_path = script_path
        self.mtime = 0.0
        self.update_script_mtime()

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

        self.cfg = self.load_config()

    def __lt__(self, other):
        return self.mtime > other.mtime  # sort by modified time descendently by default

    def update_script_mtime(self):
        assert self.script_path

        mtime = os.path.getmtime(self.script_path)

        script_config_file = get_script_config_file(self.script_path)
        if script_config_file:
            mtime = max(mtime, os.path.getmtime(script_config_file))

        if mtime > self.mtime:
            self.mtime = mtime
            return True
        else:
            return False

    def __str__(self):
        result = self.name

        if self.ext == ".link":
            result += "  (lnk)"

        # Name: show shortcut
        if self.cfg["hotkey"]:
            result += "  (%s)" % get_hotkey_abbr(self.cfg["hotkey"])

        if self.cfg["globalHotkey"]:
            result += "  (%s)" % get_hotkey_abbr(self.cfg["globalHotkey"])

        return result

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

    def get_console_title(self):
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
                if len(saved_variables[vname]) > 0:
                    last_modified_value = saved_variables[vname][0]
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

    def execute(
        self,
        args: Optional[Union[str, List[str]]] = None,
        new_window=None,
        restart_instance=None,
        close_on_exit=None,
        cd=True,
        tee=None,
        command_wrapper=True,
    ) -> bool:
        self.cfg = self.load_config()

        new_window = self.cfg["newWindow"] if new_window is None else new_window
        # TODO: Mac does not support newWindow yet
        if sys.platform == "darwin":
            new_window = False

        background = self.cfg["background"]

        if restart_instance is None:
            restart_instance = self.cfg["restartInstance"]

        if tee is None:
            tee = self.cfg["tee"]

        if not restart_instance and new_window:
            if activate_window_by_name(
                self.cfg["matchTitle"] if self.cfg["matchTitle"] else self.name
            ):
                return True

        # Get variable name value pairs
        variables = self.get_variables()

        logging.info("execute script: %s: args=%s" % (self.name, args))
        close_on_exit = (
            close_on_exit if close_on_exit is not None else self.cfg["closeOnExit"]
        )

        script_path = self.get_script_path()
        ext = self.real_ext if self.real_ext else self.ext

        # Save last executed script
        with open(_get_script_history_file(), "w") as f:
            json.dump({"file": script_path}, f)

        if ext == ".md" or ext == ".txt":
            open_in_editor(script_path)
            return True

        arg_list: List[str]
        if type(args) == str:
            arg_list = [args]
        elif type(args) == list:
            arg_list = args
        else:
            arg_list = []

        env = {**variables}

        shell = False

        if self.cfg["adk"]:
            setup_android_env(env=env)

        if self.cfg["cmake"]:
            setup_cmake(env=env)

        setup_env_var(env)

        # Setup PYTHONPATH globally (e.g. useful for vscode)
        setup_python_path(env)

        # Install packages
        if self.cfg["packages"]:
            packages = self.cfg["packages"].split()
            for pkg in packages:
                require_package(pkg)

            if "node" in packages:
                print("node package is required.")
                setup_nodejs(install=False)

        # Check if template is enabled or not
        if self.cfg["template"] is None:
            source = self.get_script_source()
            template = "{{" in source
        else:
            source = None
            template = self.cfg["template"]

        # HACK: pass current folder
        if "CWD" in os.environ:
            env["CWD"] = os.environ["CWD"]

        # Override ANDROID_SERIAL
        if "ANDROID_SERIAL" not in os.environ:
            android_serial = get_variable("ANDROID_SERIAL")
            if android_serial:
                env["ANDROID_SERIAL"] = android_serial

        if cd:
            cwd = os.path.abspath(
                os.path.join(os.getcwd(), os.path.dirname(script_path))
            )
        else:
            cwd = None

        if "CWD" in os.environ:
            cwd = os.environ["CWD"]
        logging.debug("Script.execute(): CWD: %s" % cwd)

        cmdline = self.cfg["cmdline"]
        if cmdline:
            arg_list = shlex.split(cmdline.format(SCRIPT=quote_arg(self.script_path)))

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

                background = True

                if self.cfg["runAsAdmin"]:
                    arg_list = ["start"] + arg_list

                # Disable console window for ahk
                new_window = False

                # Avoid WinError 740: The requested operation requires elevation for AutoHotkeyU64_UIA.exe
                shell = True

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
                print("OS does not support script: %s" % script_path)
                return False

        elif ext == ".js":
            # Userscript
            if script_path.endswith(".user.js"):
                updated = True
                print("(watching file change, press any key to cancel...)")
                while True:
                    if updated:
                        relpath = self.script_rel_path
                        if template:
                            relpath = os.path.dirname(relpath)
                            if len(relpath) > 0:
                                relpath += "/"
                            relpath += "generated/" + os.path.basename(
                                self.script_rel_path
                            )
                            d = os.path.join(
                                os.path.dirname(self.script_path), "generated"
                            )
                            os.makedirs(d, exist_ok=True)
                            with open(
                                os.path.join(d, os.path.basename(self.script_path)),
                                "w",
                                encoding="utf-8",
                            ) as f:
                                f.write(self.render(source=source))

                        shell_open("http://127.0.0.1:4312/scripts/" + relpath)

                    # Check if script is updated
                    updated = self.update_script_mtime()
                    if updated:
                        source = self.get_script_source()

                    # Press any key to cancel
                    if getch(timeout=0.5) is not None:
                        break

            else:
                # TODO: support template
                setup_nodejs()
                npm_install(cwd=os.path.dirname(script_path))
                arg_list = ["node", script_path] + arg_list

        elif ext == ".sh":
            if template:
                script_path = write_temp_file(
                    self.render(source=source), slugify(self.name) + ".sh"
                )

            arg_list = [script_path] + arg_list
            if self.cfg["wsl"]:
                arg_list = [
                    convert_to_unix_path(x, wsl=self.cfg["wsl"]) for x in arg_list
                ]
            bash_cmd = "bash " + _args_to_str(arg_list, shell_type="bash")
            logging.debug("bash_cmd: %s" % bash_cmd)

            arg_list = wrap_bash_commands(
                bash_cmd, wsl=self.cfg["wsl"], env=env, msys2=self.cfg["msys2"]
            )

        elif ext == ".expect":
            arg_list = wrap_bash_commands(
                "expect '%s'" % convert_to_unix_path(script_path, wsl=True),
                wsl=True,
                env=env,
            )

        elif ext == ".py" or ext == ".ipynb":
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
                    call_echo(
                        'call "%s" & conda create --name %s python=3.6'
                        % (activate, env_name)
                    )

                args_activate = ["cmd", "/c", "call", activate, env_name, "&"]

            elif self.cfg["venv"]:
                assert sys.platform == "win32"
                venv_path = os.path.expanduser("~\\venv\\%s" % self.cfg["venv"])
                if not os.path.exists(venv_path):
                    call_echo(["python", "-m", "venv", venv_path])

                args_activate = [
                    "cmd",
                    "/c",
                    "call",
                    "%s\\Scripts\\activate.bat" % venv_path,
                    "&",
                ]

            if ext == ".py":
                if self.cfg["runpy"]:
                    run_py = os.path.abspath(SCRIPT_ROOT + "/../bin/run_python.py")
                    # TODO: make it more general
                    if sys.platform == "win32":
                        if self.cfg["wsl"]:
                            run_py = convert_to_unix_path(run_py, wsl=self.cfg["wsl"])

                    # -u disables buffering so that we can get correct output during piping output
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

            if self.cfg["wsl"]:
                arg_list = wrap_wsl(arg_list, env=env)
        elif ext == ".vbs":
            assert sys.platform == "win32"

            script_abs_path = os.path.join(os.getcwd(), script_path)
            arg_list = ["cscript", "//nologo", script_abs_path] + arg_list

        elif ext == ".cpp" or ext == ".c" or ext == ".cc":
            arg_list = ["run_script", "ext/build_and_run_cpp.py", script_path]

        elif ext == ".url":
            url = self.get_script_source()
            shell_open(url)

        else:
            print("Not supported script:", ext)

        # Run commands
        if len(arg_list) > 0:
            args = arg_list
            if tee:
                log_file = os.path.join(
                    get_home_path(),
                    "Desktop",
                    "{}_{}.log".format(self.name.split("/")[-1], int(time.time())),
                )
                args = wrap_args_tee(
                    args,
                    out_file=log_file,
                )
                open_log_file(log_file)

            no_wait = False
            open_in_terminal = False
            popen_extra_args: Dict[str, Any] = {}

            if command_wrapper and not background and not self.cfg["minimized"]:
                # Add command wrapper to pause on exit
                env["CLOSE_ON_EXIT"] = "1" if close_on_exit else "0"
                args = [
                    sys.executable,
                    os.path.join(get_bin_dir(), "command_wrapper.py"),
                ] + args

            if new_window:
                if restart_instance:
                    # Close exising instances
                    close_window_by_name(self.get_console_title())
                try:
                    if sys.platform == "win32":
                        # Open in specified terminal (e.g. Windows Terminal)
                        if self.cfg["terminal"] in [
                            "wt",
                            "wsl",
                            "windowsTerminal",
                        ] and os.path.exists(WINDOWS_TERMINAL_EXEC):
                            args = wrap_args_wt(
                                args,
                                cwd=cwd,
                                title=self.get_console_title(),
                                wsl=self.cfg["wsl"],
                            )
                            no_wait = True
                            open_in_terminal = True

                        elif self.cfg["terminal"] == "alacritty" and shutil.which(
                            "alacritty"
                        ):
                            args = wrap_args_alacritty(
                                args,
                                title=self.get_console_title(),
                            )

                            # Workaround that prevents alacritty from being closed by parent terminal.
                            # The "shell = True" below is very important!
                            DETACHED_PROCESS = 0x00000008
                            CREATE_BREAKAWAY_FROM_JOB = 0x01000000
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
                            args = wrap_args_conemu(
                                args,
                                cwd=cwd,
                                title=self.get_console_title(),
                                wsl=self.cfg["wsl"],
                                always_on_top=True,
                            )
                            no_wait = True
                            open_in_terminal = True

                        else:
                            args = wrap_args_cmd(
                                args,
                                cwd=cwd,
                                title=self.get_console_title(),
                                env=env,
                            )
                            popen_extra_args["creationflags"] = (
                                subprocess.CREATE_NEW_CONSOLE
                                | subprocess.CREATE_NEW_PROCESS_GROUP
                            )
                            no_wait = True
                            open_in_terminal = True

                    elif sys.platform == "linux":
                        # args = ["tmux", "split-window"] + args

                        TERMINAL = "alacritty"
                        if TERMINAL == "gnome":
                            args = [
                                "gnome-terminal",
                                "--",
                                "bash",
                                "-c",
                                "%s || read -rsn1 -p 'Press any key to exit...'"
                                % _args_to_str(args, shell_type="bash"),
                            ]

                        elif TERMINAL == "xterm":
                            args = [
                                "xterm",
                                "-xrm",
                                "XTerm.vt100.allowTitleOps: false",
                                "-T",
                                self.get_console_title(),
                                "-e",
                                _args_to_str(args, shell_type="bash"),
                            ]
                            no_wait = True
                            open_in_terminal = True

                        elif TERMINAL == "xfce":
                            args = [
                                "xfce4-terminal",
                                "-T",
                                self.get_console_title(),
                                "-e",
                                _args_to_str(args, shell_type="bash"),
                                "--hold",
                            ]
                            no_wait = True
                            open_in_terminal = True

                        elif TERMINAL == "kitty":
                            args = [
                                "kitty",
                                "--title",
                                self.get_console_title(),
                            ] + args
                            no_wait = True
                            open_in_terminal = True

                        elif TERMINAL == "alacritty":
                            args = wrap_args_alacritty(
                                args,
                                title=self.get_console_title(),
                            )
                            no_wait = True
                            open_in_terminal = True

                    else:
                        logging.warning(
                            '"new_window" is not supported on platform "%s"'
                            % sys.platform
                        )
                except FileNotFoundError as ex:
                    new_window = False
                    no_wait = False
                    logging.warning(ex)

            elif background:
                if sys.platform == "win32":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
                    SW_HIDE = 0
                    startupinfo.wShowWindow = SW_HIDE
                    popen_extra_args["startupinfo"] = startupinfo

                    DETACHED_PROCESS = 0x00000008
                    popen_extra_args["creationflags"] = (
                        subprocess.CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS
                    )

                    popen_extra_args["close_fds"] = True
                    no_wait = True

                else:
                    logging.warning(
                        '"background" is not supported on platform %s' % sys.platform
                    )

            elif self.cfg["minimized"]:
                if sys.platform == "win32":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
                    SW_MINIMIZE = 6
                    startupinfo.wShowWindow = SW_MINIMIZE
                    popen_extra_args["startupinfo"] = startupinfo

                    popen_extra_args["creationflags"] = (
                        subprocess.CREATE_NEW_CONSOLE
                        | subprocess.CREATE_NEW_PROCESS_GROUP
                    )
                    popen_extra_args["close_fds"] = True
                    no_wait = True

                else:
                    logging.warning(
                        '"minimized" is not supported on platform %s' % sys.platform
                    )

            if no_wait:
                if sys.platform == "linux":
                    popen_extra_args["start_new_session"] = True

            if self.cfg["runAsAdmin"]:
                # Passing environmental variables
                args = wrap_args_cmd(
                    args,
                    cwd=cwd,
                    title=self.get_console_title(),
                    env=env,
                )

                logging.debug("run_elevated(): args=%s" % args)
                return_code = run_elevated(
                    args, wait=not no_wait, show_terminal_window=not open_in_terminal
                )
                if no_wait:
                    return True
                else:
                    return return_code == 0

            else:
                logging.debug("cmdline: %s" % args)
                ps = subprocess.Popen(
                    args=args,
                    env={**os.environ, **env},
                    cwd=cwd,
                    shell=shell,
                    **popen_extra_args,
                )
                success = True
                if not no_wait:
                    success = ps.wait() == 0

                # if not new_window and not close_on_exit:
                #     print("(press enter to exit...)")
                #     input()

                return success

        else:  # no args
            return True

    def get_variable_names(self):
        with open(self.script_path, "r", encoding="utf-8") as f:
            s = f.read()
            variables = re.findall(r"\b([A-Z_$][A-Z_$0-9]{3,})\b", s)

        # Remove duplicates
        variables = list(set(variables))

        # Convert private variable to global namespace
        prefix = self.get_public_variable_prefix()
        variables = [prefix + v if v.startswith("_") else v for v in variables]

        variables = [x for x in variables if x not in RESERVED_VARIABLE_NAMES]

        return variables


def find_script(patt: str) -> Optional[str]:
    if os.path.exists(patt):
        return os.path.abspath(patt)

    script_path = get_absolute_script_path(patt)
    if os.path.exists(script_path):
        return script_path

    # Fuzzy search
    for _, script_root_dir in get_script_directories():
        name_no_ext, _ = os.path.splitext(patt.lstrip("/"))
        path = os.path.join(script_root_dir, "**", name_no_ext + ".*")

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


def run_script(
    file=None,
    args=[],
    variables=None,
    console_title=None,
    config_override=None,
    template=None,
    new_window=False,  # should not start a new window by default
    restart_instance=False,
    cd=True,
    tee=False,
):
    start_time = time.time()
    if file is None:
        file = get_last_script()

    # Print command line arguments
    logging.info(
        "run_script: %s"
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
        restart_instance=restart_instance,
        new_window=new_window,
        args=args,
        cd=cd,
        tee=tee,
    )
    if not ret:
        raise Exception("[ERROR] %s returns non zero" % file)

    # Restore title
    if console_title and sys.platform == "win32":
        ctypes.windll.kernel32.SetConsoleTitleA(saved_title)

    end_time = time.time()
    logging.info(
        "run_script: %s finished in %s" % (file, format_time(end_time - start_time)),
    )


def start_script(file=None, restart_instance=None):
    if file is None:
        file = get_last_script()

    script_path = find_script(file)
    if script_path is None:
        raise Exception('[ERROR] Cannot find script: "%s"' % file)

    script = Script(script_path)
    if not script.execute(restart_instance=restart_instance):
        raise Exception("[ERROR] %s returns non zero" % file)


def get_script_default_config() -> Dict[str, Any]:
    return {
        "adk": False,
        "autoRun": False,
        "background": False,
        "closeOnExit": True,
        "cmake": "",
        "cmdline": "",
        "conda": "",
        "globalHotkey": "",
        "hotkey": "",
        "matchClipboard": "",
        "matchTitle": "",
        "minimized": False,
        "msys2": False,
        "newWindow": True,
        "packages": "",
        "restartInstance": False,
        "runAsAdmin": False,
        "runAtStartup": False,
        "runpy": True,
        "tee": False,
        "template": None,
        "terminal": "alacritty",
        "title": "",
        "venv": "",
        "wsl": False,
    }


def get_script_config_file(script_path, auto_create=False) -> Optional[str]:
    f = os.path.splitext(script_path)[0] + ".config.yaml"
    if auto_create or os.path.exists(f):
        return f

    f = os.path.join(os.path.dirname(script_path), "default.config.yaml")
    if os.path.exists(f):
        return f

    return None


def load_script_config(script_path) -> Dict[str, Any]:
    script_config_file = get_script_config_file(script_path)
    if script_config_file:
        with open(script_config_file, "r") as f:
            data = yaml.load(f.read(), Loader=yaml.FullLoader)
    else:
        data = None

    config = get_script_default_config()

    # override default config
    if data is not None:
        for k, v in data.items():
            config[k] = v

    return config


def update_script_config(kvp, script_file):
    default_config = get_script_default_config()
    script_config_file = get_script_config_file(script_file)
    if script_config_file is not None and not os.path.exists(script_config_file):
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

        try:
            fh = open(LOCK_PATH, "w")
            fcntl.lockf(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except EnvironmentError as err:
            if fh is not None:
                return True
            else:
                raise

    return False


def _get_script_access_time_file() -> str:
    config_file = os.path.join(get_data_dir(), "script_access_time.json")
    return config_file


def update_script_access_time(script):
    config_file = _get_script_access_time_file()
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            data = json.load(f)
    else:
        data = {}

    data[script.script_path] = time.time()

    with open(config_file, "w") as f:
        json.dump(data, f, indent=4)


_script_access_time_file_mtime = 0.0
_cached_script_access_time: Dict = {}


def get_all_script_access_time() -> Tuple[Dict, float]:
    global _script_access_time_file_mtime
    global _cached_script_access_time

    config_file = _get_script_access_time_file()
    if not os.path.exists(config_file):
        return {}, 0

    mtime = os.path.getmtime(config_file)
    if mtime > _script_access_time_file_mtime:
        _script_access_time_file_mtime = mtime
        with open(config_file, "r") as f:
            _cached_script_access_time = json.load(f)

    return _cached_script_access_time, _script_access_time_file_mtime


def get_scripts_recursive(directory) -> Iterator[str]:
    def should_ignore(dir, file):
        if file == "tmp" or file == "generated":
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
            if ext not in SCRIPT_EXTENSIONS:
                continue
            if ".win" in file and sys.platform != "win32":
                continue
            if ".linux" in file and sys.platform != "linux":
                continue
            if ".mac" in file and sys.platform != "darwin":
                continue

            yield os.path.join(root, file)


def get_all_scripts() -> Iterator[str]:
    for _, script_path in get_script_directories():
        files = get_scripts_recursive(script_path)
        for file in files:
            # File has been removed during iteration
            if not os.path.exists(file):
                continue

            # Hide files starting with '_'
            base_name = os.path.basename(file)
            if base_name.startswith("_"):
                continue

            yield file


def reload_scripts(
    script_list: List[Script],
    autorun=True,
    startup=False,
    on_progress: Optional[Callable[[], None]] = None,
) -> bool:
    script_dict = {script.script_path: script for script in script_list}
    script_list.clear()
    clear_env_var_explorer()

    any_script_reloaded = False
    for i, file in enumerate(get_all_scripts()):
        if i % 20 == 0:
            if on_progress is not None:
                on_progress()

        if file in script_dict:
            script = script_dict[file]
            reloaded = script.update_script_mtime()
        else:
            script = Script(file)
            reloaded = True

        if reloaded:
            any_script_reloaded = True
            should_run_script = False
            if script.cfg["autoRun"] and autorun:
                logging.info("autorun: %s" % script.name)
                should_run_script = True
            if script.cfg["runAtStartup"] and startup:
                logging.info("runAtStartup: %s" % script.name)
                should_run_script = True

            # Check if auto run script
            if should_run_script:
                try:
                    script.execute(new_window=False, command_wrapper=False)
                except Exception as ex:
                    logging.warning(ex)

        bisect.insort(script_list, script)

    return any_script_reloaded


def render_script(script_path) -> str:
    script = Script(script_path)
    return script.render()
