import ctypes
import glob
import json
import locale
import logging
import os
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time

import yaml

from _android import setup_android_env
from _browser import open_url
from _editor import open_in_vscode
from _filelock import FileLock
from _pkgmanager import require_package
from _shutil import (
    CONEMU_INSTALL_DIR,
    activate_window_by_name,
    call_echo,
    convert_to_unix_path,
    exec_ahk,
    format_time,
    get_ahk_exe,
    get_home_path,
    load_yaml,
    npm_install,
    print2,
    quote_arg,
    run_at_startup,
    run_elevated,
    save_yaml,
    setup_nodejs,
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
    ".ps1",
    ".py",
    ".sh",
    ".vbs",  # Windows specific,
}

DEFAULT_TERMINAL_FONT_SIZE = 8
if sys.platform == "win32":
    WINDOWS_TERMINAL_EXEC = (
        os.environ["LOCALAPPDATA"] + "\\Microsoft\\WindowsApps\\wt.exe"
    )


def get_data_dir():
    data_dir_file = os.path.abspath(
        os.path.join(SCRIPT_ROOT, "..", "config", "data_dir.txt")
    )
    if os.path.exists(data_dir_file):
        with open(data_dir_file, "r") as f:
            data_dir = f.read().strip()
    else:
        data_dir = os.path.abspath("%s/../tmp/data/%s" % (SCRIPT_ROOT, platform.node()))
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_script_root():
    return os.path.abspath(SCRIPT_ROOT + "/../scripts")


def get_script_directories():
    directories = []
    directories.append(("", get_script_root()))

    config_file = os.path.join(get_data_dir(), "script_directories.txt")
    if not os.path.exists(config_file):
        pathlib.Path(config_file).touch()

    with open(config_file) as f:
        for line in f.read().splitlines():
            if line:
                cols = line.split("|")
                if len(cols) == 1:
                    directories.append([os.path.basename(cols[0]), cols[0]])
                elif len(cols) == 2:
                    directories.append([cols[0], cols[1]])
                else:
                    raise Exception("Invalid line in {}: {}".format(config_file, line))

    return directories


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

    bash = ""

    if env is not None:
        for k, v in env.items():
            bash += "export {}='{}'\n".format(k, v)

    if type(commands) in [list, tuple]:
        bash += _args_to_str(commands)
    else:
        bash += commands

    # To create a temp sh files to invoke commands to avoid command being parsed
    # by current shell
    logging.debug("WSL commands: {}".format(bash))
    tmp_sh_file = write_temp_file(bash, ".sh")
    tmp_sh_file = convert_to_unix_path(tmp_sh_file, wsl=True)

    # # Escape dollar sign? Why?
    # commands = commands.replace("$", r"\$")
    # return ["bash.exe", "-c", commands]

    return ["bash", "-c", tmp_sh_file]


def wrap_bash_commands(commands, wsl=False, env=None):
    assert type(commands) == str

    if sys.platform == "win32":
        if wsl:  # WSL (Windows Subsystem for Linux)
            return wrap_wsl(commands)

        else:
            if env is not None:
                env["MSYS_NO_PATHCONV"] = "1"  # Disable path conversion
                env["CHERE_INVOKING"] = "1"  # stay in the current working directory
                env["MSYSTEM"] = "MINGW64"
                # env["MSYS2_PATH_TYPE"] = "inherit"

            tmp_sh_file = write_temp_file(commands, ".sh")

            msys2_bash_search_list = [
                r"C:\Program Files\Git\bin\bash.exe",
                r"C:\msys64\usr\bin\bash.exe",
            ]

            bash = None
            for f in msys2_bash_search_list:
                if os.path.exists(f):
                    bash = f
                    break

            if bash is None:
                raise Exception("Cannot find MinGW bash.exe")
            return [bash, "--login", "-i", tmp_sh_file]

    else:  # Linux
        tmp_sh_file = write_temp_file(commands, ".sh")
        return ["bash", "-i", tmp_sh_file]


def exec_cmd(cmd):
    assert sys.platform == "win32"
    file_name = write_temp_file(cmd, ".cmd")
    args = ["cmd.exe", "/c", file_name]
    subprocess.check_call(args)


def _args_to_str(args, single_quote=False, powershell=False):
    assert type(args) in [list, tuple]
    if powershell:
        return " ".join(
            [x.replace(" ", "` ").replace("(", "`(").replace(")", "`)") for x in args]
        )
    else:
        return " ".join(
            [
                quote_arg(x, single_quote=single_quote, powershell=powershell)
                for x in args
            ]
        )


def get_variable_file():
    variable_file = os.path.join(get_data_dir(), "variables.json")
    return variable_file


def get_all_variables():
    file = get_variable_file()

    with FileLock("access_variable"):
        if not os.path.exists(file):
            return {}

        with open(file, "r", encoding="utf-8") as f:
            variables = json.load(f)
            return variables


def get_script_variables(script):
    all_vars = get_all_variables()
    vars = {}
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


def get_python_path(script_path):
    python_path = []

    script_root = os.path.abspath(SCRIPT_ROOT + "/../scripts")
    python_path.append(os.path.join(script_root, "r"))

    if script_path is not None:
        parent_dir = os.path.dirname(os.path.join(os.getcwd(), script_path))
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
        env["PYTHONPATH"] = ":".join(python_path)
    else:
        env["PYTHONPATH"] = os.pathsep.join(python_path)


def wrap_args_tee(args, out_file):
    assert type(args) is list

    s = (
        _args_to_str(args, powershell=True)
        + r" *>&1 | Tee-Object -FilePath %s" % out_file
    )
    tmp_file = write_temp_file(s, ".ps1")
    logging.debug('wrap_args_tee(file="%s"): %s' % (tmp_file, s))
    return ["powershell", tmp_file]


def wrap_args_cmd(args, title=None, cwd=None, env=None, close_on_exit=None):
    assert type(args) is list

    cmd_args = "cmd /c "

    if title:
        cmd_args += "title %s&" % quote_arg(title)

    if cwd:
        cmd_args += "cd /d %s&" % quote_arg(cwd)

    if env:
        for k, v in env.items():
            cmd_args += "&".join(['set "%s=%s"' % (k, v)]) + "&"

    cmd_args += _args_to_str(args)

    # Pause on error
    if close_on_exit:
        cmd_args += "||pause"
    else:
        cmd_args += "&pause"

    return cmd_args


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
        # "initialCols": 140,
        # "initialRows": 40,
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


def wrap_args_alacritty(
    args,
    title=None,
    font_size=DEFAULT_TERMINAL_FONT_SIZE,
    font=None,
    borderless=False,
    position=None,
    padding=None,
    **kwargs,
):
    assert isinstance(args, list)
    # https://github.com/alacritty/alacritty/blob/master/alacritty.yml
    if sys.platform != "windows":
        dest_path = os.path.expandvars(r"%APPDATA%\alacritty\alacritty.yml")
    else:
        dest_path = os.path.expanduser(".config/alacritty/alacritty.yml")
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    src_path = os.path.abspath(SCRIPT_ROOT + "/../settings/alacritty.yml")
    shutil.copy(src_path, dest_path)

    out = [
        "alacritty",
        "-o",
        f"font.size={font_size}",
    ]

    if font is not None:
        out += [f"font.normal.family={font}"]
    if borderless:
        out += ["window.decorations=none"]
    if position:
        out += [f"window.position.x={position[0]}", f"window.position.y={position[1]}"]
    if padding is not None:
        out += [f"window.padding.x={padding}", f"window.padding.y={padding}"]

    if title:
        out += ["--title", title]

    # HACK: alacritty handles spaces in a weird way
    if sys.platform == "win32":
        args = ['"' + x + '"' if " " in x else x for x in args]
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
    def __init__(self, script_path, name=None):
        if not os.path.isfile(script_path):
            raise Exception("Script file does not exist.")

        script_path = os.path.abspath(script_path)

        # Script display name
        if name:
            self.name = name
        else:
            self.name = script_path

            # Convert absolute path to relative path
            self.name = get_relative_script_path(self.name)

            # Strip extension
            self.name, _ = os.path.splitext(self.name)

        self.ext = os.path.splitext(script_path)[1].lower()  # Extension / script type
        self.override_variables = None
        self.console_title = None
        self.script_path = script_path

        # Deal with links
        if os.path.splitext(script_path)[1].lower() == ".link":
            self.real_script_path = (
                open(script_path, "r", encoding="utf-8").read().strip()
            )
            self.real_ext = os.path.splitext(self.real_script_path)[1].lower()

            self.check_link_existence()
        else:
            self.real_script_path = None
            self.real_ext = None

        self.cfg = self.load_config()

    def __str__(self):
        result = self.name

        if self.ext == ".link":
            result += " [lnk]"

        # Name: show shortcut
        if self.cfg["hotkey"]:
            result += "  (%s)" % self.cfg["hotkey"].lower().replace(
                "win+", "#"
            ).replace("ctrl+", "^").replace("alt+", "!").replace("shift+", "+")

        if self.cfg["globalHotkey"]:
            result += "  (%s)" % self.cfg["globalHotkey"].lower().replace(
                "win+", "#"
            ).replace("ctrl+", "^").replace("alt+", "!").replace("shift+", "+")

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

    def render(self, variables=None):
        if variables is None:
            variables = self.get_variables()

        script_path = (
            self.real_script_path if self.real_script_path else self.script_path
        )

        if not self.check_link_existence():
            return

        if self.ext in [".bat", ".cmd"]:
            encoding = locale.getpreferredencoding()
        else:
            encoding = "utf-8"

        with open(script_path, "r", encoding=encoding) as f:
            source = f.read()

        cwd = os.getcwd()
        script_dir = os.path.dirname(script_path)
        if script_dir:
            os.chdir(script_dir)

        result = render_template(source, variables)

        os.chdir(cwd)
        return result

    def set_override_variables(self, variables):
        self.override_variables = variables

    def get_variables(self):
        vnames = self.get_variable_names()
        all_variables = get_all_variables()
        variables = {}
        for vname in vnames:
            if vname in all_variables:
                if len(all_variables[vname]) > 0:
                    last_modified_value = all_variables[vname][0]
                    if last_modified_value:
                        variables[vname] = last_modified_value

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
        args=None,
        new_window=None,
        restart_instance=None,
        close_on_exit=None,
        cd=True,
        tee=None,
    ):
        new_window = self.cfg["newWindow"] if (new_window is None) else new_window
        # TODO: Mac does not support newWindow yet
        if sys.platform == "darwin":
            new_window = False

        if restart_instance is None:
            restart_instance = self.cfg["restartInstance"]

        if not restart_instance and new_window:
            if activate_window_by_name(self.name):
                return True

        self.cfg = self.load_config()
        variables = self.get_variables()

        logging.debug("execute(args=%s)" % args)
        close_on_exit = (
            close_on_exit if close_on_exit is not None else self.cfg["closeOnExit"]
        )

        script_path = (
            self.real_script_path if self.real_script_path else self.script_path
        )
        ext = self.real_ext if self.real_ext else self.ext

        # Save last executed script
        with open(_get_script_history_file(), "w") as f:
            json.dump({"file": script_path}, f)

        if ext == ".md":
            open_in_vscode(script_path)
            return True

        if type(args) == str:
            args = [args]
        elif type(args) == list:
            args = args
        else:
            args = []

        env = {}

        shell = False

        if self.cfg["adk"]:
            setup_android_env(env=env)

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

        if ext == ".ps1":
            if sys.platform == "win32":
                if self.cfg["template"]:
                    ps_path = write_temp_file(
                        self.render(), slugify(self.name) + ".ps1"
                    )
                else:
                    ps_path = os.path.abspath(script_path)

                args = [
                    "PowerShell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "unrestricted",
                    "-file",
                    ps_path,
                ] + args

        elif ext == ".ahk":
            if sys.platform == "win32":
                # HACK: add python path to env var
                env["PYTHONPATH"] = SCRIPT_ROOT

                if self.cfg["template"]:
                    script_path = write_temp_file(
                        self.render(),
                        os.path.join(
                            "GeneratedAhkScript/", os.path.basename(self.script_path)
                        ),
                    )
                else:
                    script_path = os.path.abspath(script_path)

                args = [get_ahk_exe(), script_path]

                self.cfg["background"] = True

                if self.cfg["runAsAdmin"]:
                    args = ["start"] + args

                # Disable console window for ahk
                new_window = False

                # Avoid WinError 740: The requested operation requires elevation for AutoHotkeyU64_UIA.exe
                shell = True

        elif ext == ".cmd" or ext == ".bat":
            if sys.platform == "win32":
                if self.cfg["template"]:
                    batch_file = write_temp_file(
                        self.render(), slugify(self.name) + ".cmd"
                    )
                else:
                    batch_file = os.path.abspath(script_path)

                # "call" must be used if there are spaces in batch file name
                args = ["cmd.exe", "/c", "call", batch_file] + args
            else:
                print("OS does not support script: %s" % script_path)
                return False

        elif ext == ".js":
            if script_path.endswith(".user.js"):  # is user script
                open_url("file://" + script_path.replace("\\", "/"))
            else:
                # TODO: support template
                setup_nodejs()
                npm_install(cwd=os.path.dirname(script_path))
                args = ["node", script_path] + args

        elif ext == ".sh":
            if self.cfg["template"]:
                script_path = write_temp_file(self.render(), slugify(self.name) + ".sh")

            args = [script_path] + args
            if self.cfg["wsl"]:
                args = [convert_to_unix_path(x, wsl=self.cfg["wsl"]) for x in args]
            bash_cmd = "bash " + _args_to_str(args, single_quote=True)
            logging.debug("bash_cmd: %s" % bash_cmd)

            args = wrap_bash_commands(bash_cmd, wsl=self.cfg["wsl"], env=env)

        elif ext == ".expect":
            args = wrap_bash_commands(
                "expect '%s'" % convert_to_unix_path(script_path, wsl=True),
                wsl=True,
                env=env,
            )

        elif ext == ".py" or ext == ".ipynb":
            python_exec = sys.executable

            if self.cfg["template"] and ext == ".py":
                python_file = write_temp_file(self.render(), slugify(self.name) + ".py")
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

                    args = args_activate + [python_exec, run_py, python_file] + args
                else:
                    args = args_activate + [python_exec, python_file] + args
            elif ext == ".ipynb":
                args = args_activate + ["jupyter", "notebook", python_file] + args

                # HACK: always use new window for jupyter notebook
                self.cfg["newWindow"] = True
            else:
                assert False

            if self.cfg["wsl"]:
                args = wrap_wsl(args, env=env)
        elif ext == ".vbs":
            assert sys.platform == "win32"

            script_abs_path = os.path.join(os.getcwd(), script_path)
            args = ["cscript", "//nologo", script_abs_path] + args

        elif ext == ".cpp" or ext == ".c" or ext == ".cc":
            args = ["run_script", "ext/build_and_run_cpp.py", script_path]

        else:
            print("Not supported script:", ext)

        # Run commands
        if args is not None and len(args) > 0:
            if tee is None:
                tee = self.cfg["tee"]
            if tee:
                args = wrap_args_tee(
                    args,
                    out_file=os.path.join(
                        get_home_path(),
                        "Desktop",
                        "{}_{}.log".format(self.name.split("/")[-1], int(time.time())),
                    ),
                )

            # Check if run as admin
            if self.cfg["runAsAdmin"]:
                if sys.platform == "win32":
                    args = wrap_args_cmd(
                        args,
                        cwd=cwd,
                        title=self.get_console_title(),
                        env=env,
                        close_on_exit=close_on_exit,
                    )

                    logging.debug("run_elevated(%s)" % args)
                    run_elevated(args, wait=(not new_window))
                    return True

            no_wait = False
            popen_extra_args = {}

            if new_window:
                if restart_instance:
                    # Close exising instances
                    if sys.platform == "win32":
                        exec_ahk(
                            "SetTitleMatchMode RegEx\nWinClose, ^"
                            + re.escape(self.get_console_title())
                            + ", , , .*?- Visual Studio Code",
                            wait=True,
                        )

                if sys.platform == "win32":
                    if close_on_exit:
                        args = ["cmd", "/c", "pause_on_error.cmd"] + args
                    else:
                        args = ["cmd", "/c", "pause_on_exit.cmd"] + args

                    if not self.cfg["runAsAdmin"]:
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
                            % _args_to_str(args, single_quote=True),
                        ]

                    elif TERMINAL == "xterm":
                        args = [
                            "xterm",
                            "-xrm",
                            "XTerm.vt100.allowTitleOps: false",
                            "-T",
                            self.get_console_title(),
                            "-e",
                            _args_to_str(args),
                        ]
                        no_wait = True

                    elif TERMINAL == "xfce":
                        args = [
                            "xfce4-terminal",
                            "-T",
                            self.get_console_title(),
                            "-e",
                            _args_to_str(args),
                            "--hold",
                        ]
                        no_wait = True

                    elif TERMINAL == "kitty":
                        args = [
                            "kitty",
                            "--title",
                            self.get_console_title(),
                        ] + args
                        no_wait = True

                    elif TERMINAL == "alacritty":
                        require_package("alacritty")
                        args = wrap_args_alacritty(
                            args,
                            title=self.get_console_title(),
                        )

                else:
                    logging.warn(
                        '"new_window" is not supported on platform "%s"' % sys.platform
                    )

            elif self.cfg["background"]:
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
                    logging.warn(
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
                    logging.warn(
                        '"minimized" is not supported on platform %s' % sys.platform
                    )

            logging.debug("subprocess.Popen(): args=%s" % args)
            if no_wait:
                if sys.platform == "linux":
                    popen_extra_args["start_new_session"] = True

            ps = subprocess.Popen(
                args=args,
                env={**variables, **os.environ, **env},
                cwd=cwd,
                shell=shell,
                **popen_extra_args,
            )
            if not no_wait:
                return ps.wait() == 0

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

        return variables


def find_script(patt):
    if os.path.exists(patt):
        return os.path.abspath(patt)

    script_path = os.path.abspath(SCRIPT_ROOT + "/../scripts/" + patt.lstrip("/"))
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


def run_script(
    file=None,
    args=[],
    variables=None,
    console_title=None,
    overwrite_meta=None,
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
    logging.info("run_script: %s" % _args_to_str([file] + args))

    script_path = find_script(file)
    if script_path is None:
        raise Exception('Cannot find script: "%s"' % file)

    script = Script(script_path)

    if console_title:
        script.console_title = console_title

    if template is not None:
        script.cfg["template"] = template

    if overwrite_meta:
        for k, v in overwrite_meta.items():
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


def get_script_default_config():
    return {
        "adk": False,
        "autoRun": False,
        "background": False,
        "closeOnExit": True,
        "conda": "",
        "globalHotkey": "",
        "hotkey": "",
        "minimized": False,
        "newWindow": True,
        "packages": "",
        "restartInstance": False,
        "runAsAdmin": False,
        "runAtStartup": False,
        "runpy": True,
        "tee": False,
        "template": False,
        "terminal": "wt",
        "title": "",
        "venv": "",
        "wsl": False,
    }


def get_script_config_file(script_path):
    return os.path.splitext(script_path)[0] + ".config.yaml"


def load_script_config_file2(script_path):
    f = get_script_config_file(script_path)
    if os.path.exists(f):
        return f

    f = os.path.join(os.path.dirname(script_path), "default.yaml")
    if os.path.exists(f):
        return f


def load_script_config(script_path):
    script_config_file = load_script_config_file2(script_path)
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


def is_instance_running():
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


def _get_script_access_time_file():
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


def get_all_script_access_time():
    self = get_all_script_access_time

    if not hasattr(self, "mtime"):
        self.mtime = 0

    config_file = _get_script_access_time_file()
    if not os.path.exists(config_file):
        return {}, 0

    mtime = os.path.getmtime(config_file)
    if mtime > self.mtime:
        with open(config_file, "r") as f:
            self.cached_data = json.load(f)

        self.mtime = mtime

    return self.cached_data, self.mtime


def get_scripts_recursive(directory):
    def should_ignore(dir, file):
        if file == "tmp":
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


def script_updated():
    if not hasattr(script_updated, "last_mtime"):
        script_updated.last_mtime = 0
        script_updated.file_list = None

    mtime = 0
    file_list = []
    for _, d in get_script_directories():
        for f in get_scripts_recursive(d):
            mtime = max(mtime, os.path.getmtime(f))
            script_config_file = load_script_config_file2(f)
            file_list.append(f)

            # Check if config file is updated
            if script_config_file:
                mtime = max(mtime, os.path.getmtime(script_config_file))

    if (mtime > script_updated.last_mtime) or (file_list != script_updated.file_list):
        script_updated.last_mtime = mtime
        script_updated.file_list = file_list
        return True
    else:
        return False


def get_all_scripts():
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


def reload_scripts(script_list, modified_time, autorun=True):
    if not script_updated():
        return False

    # TODO: only update modified scripts
    script_list.clear()

    for file in get_all_scripts():
        script = Script(file)

        mtime = os.path.getmtime(file)
        script_config_file = load_script_config_file2(file)
        if script_config_file:
            mtime = max(mtime, os.path.getmtime(script_config_file))
        if (
            script.script_path not in modified_time
            or mtime > modified_time[script.script_path]
        ):
            # Check if auto run script
            if script.cfg["autoRun"] and autorun:
                logging.info("autorun: %s" % script.name)
                script.execute(new_window=False)

            # Check if the script should run at startup
            if script.cfg["runAtStartup"] and autorun:
                logging.info("runAtStartup: %s" % script.name)
                run_at_startup(
                    name=script.name, cmdline='"start_script" "%s"' % script.script_path
                )

        modified_time[script.script_path] = mtime

        script_list.append(script)

    return True


def render_script(script_path):
    script = Script(script_path)
    return script.render()
