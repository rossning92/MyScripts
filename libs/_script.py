import ctypes
import glob
import json
import locale
import os
import pathlib
import platform
import re
import shlex
import subprocess
import sys
import tempfile
import time

import jinja2
import yaml

from _appmanager import get_executable
from _editor import open_in_vscode
from _shutil import (
    call_echo,
    conemu_wrap_args,
    convert_to_unix_path,
    exec_ahk,
    get_ahk_exe,
    get_script_root,
    print2,
    run_elevated,
    setup_nodejs,
    write_temp_file,
)

SCRIPT_EXTENSIONS = {
    ".sh",
    ".js",
    ".link",
    ".py",
    ".ipynb",  # Python
    ".cmd",
    ".bat",
    ".ps1",
    ".ahk",
    ".vbs",  # Windows specific,
    ".md",
}


def get_data_dir():
    data_dir = os.path.abspath(
        "{}/../tmp/data/{}".format(os.path.dirname(__file__), platform.node())
    )
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_script_directories():
    directories = []
    directories.append(("", os.path.abspath(os.path.dirname(__file__) + "/../scripts")))

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


def set_console_title(title):
    if platform.system() == "Windows":
        old = get_console_title()
        win_title = title.encode(locale.getpreferredencoding())
        ctypes.windll.kernel32.SetConsoleTitleA(win_title)
        return old

    return None


def get_console_title():
    if platform.system() == "Windows":
        MAX_BUFFER = 260
        saved_title = (ctypes.c_char * MAX_BUFFER)()
        ret = ctypes.windll.kernel32.GetConsoleTitleA(saved_title, MAX_BUFFER)
        assert ret > 0
        return saved_title.value.decode(locale.getpreferredencoding())

    return None


def wrap_wsl(commands):
    if not os.path.exists(r"C:\Windows\System32\bash.exe"):
        raise Exception("WSL (Windows Subsystem for Linux) is not installed.")

    if type(commands) in [list, tuple]:
        commands = _args_to_str(commands)

    # To create a temp sh files to invoke commands to avoid command being parsed
    # by current shell
    tmp_sh_file = write_temp_file(commands, ".sh")
    tmp_sh_file = convert_to_unix_path(tmp_sh_file, wsl=True)

    # # Escape dollar sign? Why?
    # commands = commands.replace("$", r"\$")
    # return ["bash.exe", "-c", commands]

    return ["bash", "-c", tmp_sh_file]


def wrap_bash_commands(commands, wsl=False, env=None):
    assert type(commands) == str

    if os.name == "nt" and wsl:  # WSL (Windows Subsystem for Linux)
        return wrap_wsl(commands)

    elif os.name == "nt":
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
        return ["bash", "-c", commands]


def exec_cmd(cmd):
    assert os.name == "nt"
    file_name = write_temp_file(cmd, ".cmd")
    args = ["cmd.exe", "/c", file_name]
    subprocess.check_call(args)


def _args_to_str(args):
    if platform.system() == "Windows":
        args = ['"%s"' % a if " " in a else a for a in args]
    else:
        args = [shlex.quote(x) for x in args]
    return " ".join(args)


def get_variable_file():
    variable_file = os.path.join(get_data_dir(), "variables.json")
    return variable_file


def get_all_variables():
    file = get_variable_file()
    if not os.path.exists(file):
        return {}

    with open(file, "r") as f:
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


def read_setting(setting, name, val):
    file = os.path.join(get_data_dir(), "%s.json" % setting)

    try:
        with open(file, "r") as f:
            data = json.load(f)
    except IOError:
        return None

    if name not in data:
        return None

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


def get_variable(name):
    with open(get_variable_file(), "r") as f:
        variables = json.load(f)

    if name not in variables:
        return None

    return variables[name][0]


def set_variable(name, val):
    file = get_variable_file()
    with open(file, "r") as f:
        variables = json.load(f)

    if name not in variables:
        variables[name] = []
    vals = variables[name]

    try:
        vals.remove(val)
    except ValueError:
        pass
    vals.insert(0, val)

    with open(file, "w") as f:
        json.dump(variables, f, indent=2)


def input2(message, name):
    val = get_variable(name)
    user_input = input("%s (default: %s): " % (message, val))
    if not user_input and val:
        return val

    set_variable(name, val)
    return user_input


def get_python_path(script_path):
    python_path = []

    script_root = os.path.abspath(os.path.dirname(__file__) + "/../scripts/r")
    python_path.append(script_root)

    if script_path is not None:
        parent_dir = os.path.dirname(os.path.join(os.getcwd(), script_path))
        python_path.append(parent_dir)
        while parent_dir.startswith(script_root):
            python_path.append(parent_dir)
            parent_dir = os.path.abspath(parent_dir + "/../")

    python_path.append(os.path.dirname(__file__))

    return python_path


def setup_python_path(script_path=None):
    python_path = get_python_path(script_path)
    os.environ["PYTHONPATH"] = os.pathsep.join(python_path)


def wrap_args_cmd(
    args, title=None, cwd=None, script_path=None, env=None, close_on_exit=True
):
    bin_path = os.path.abspath(os.path.dirname(__file__) + "/../bin")

    args2 = ["cmd", "/c"]

    if title:
        args2 += ["title", title, "&"]

    if cwd:
        args2 += ["cd", "/d", cwd, "&"]

    args2 += [
        "set",
        "PATH=" + bin_path + ";%PATH%",
        "&",
    ]

    if script_path:
        args2 += [
            "set",
            "PYTHONPATH=" + os.pathsep.join(get_python_path(script_path)),
            "&",
        ]

    if env:
        for k, v in env.items():
            args2 += ["set", '"%s=%s"' % (k, v), "&"]

    args2 += args

    # Pause on error
    if close_on_exit:
        args2 += ["||", "pause"]
    else:
        args2 += ["&", "pause"]

    return args2


def wt_wrap_args(
    args,
    wsl=False,
    title=None,
    close_on_exit=True,
    cwd=None,
    font_size=10,
    icon=None,
    opacity=1.0,
):
    THEME = {
        "name": "Dracula",
        "cursorColor": "#F8F8F2",
        "selectionBackground": "#44475A",
        "background": "#282A36",
        "foreground": "#F8F8F2",
        "black": "#21222C",
        "blue": "#BD93F9",
        "cyan": "#8BE9FD",
        "green": "#50FA7B",
        "purple": "#FF79C6",
        "red": "#FF5555",
        "white": "#F8F8F2",
        "yellow": "#F1FA8C",
        "brightBlack": "#6272A4",
        "brightBlue": "#D6ACFF",
        "brightCyan": "#A4FFFF",
        "brightGreen": "#69FF94",
        "brightPurple": "#FF92DF",
        "brightRed": "#FF6E6E",
        "brightWhite": "#FFFFFF",
        "brightYellow": "#FFFFA5",
    }

    if sys.platform != "win32":
        raise Exception("the function can only be called on windows platform.")

    # Escape simicolons used in wt command.
    args = [x.replace(";", r"\;") for x in args]

    CONFIG_FILE = os.path.expandvars(
        r"%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"
    )

    with open(CONFIG_FILE, "r") as f:
        lines = f.read().splitlines()

    lines = [x for x in lines if not x.lstrip().startswith("//")]
    data = json.loads("\n".join(lines))

    data["profiles"]["defaults"]["colorScheme"] = "Dracula"
    data["profiles"]["defaults"]["fontSize"] = 10
    data["schemes"] = [THEME]

    updated = False
    if title:
        filtered = list(filter(lambda x: x["name"] == title, data["profiles"]["list"]))
        profile = {
            "name": title,
            "hidden": False,
            "commandline": "wsl -d Ubuntu" if wsl else "cmd.exe",
            "closeOnExit": "graceful" if close_on_exit else "never",
            "suppressApplicationTitle": True,
            "fontSize": font_size,
        }

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

        return ["wt", "-p", title] + args
    else:
        return ["wt"] + args


class Script:
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath="./"))

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

    def __init__(self, script_path, name=None):
        self.return_code = 0

        # TODO: jinja2 doesn't support '\' in path. Seems fixed?
        script_path = script_path.replace(os.path.sep, "/")

        # Script display name
        if name:
            self.name = name
        else:
            self.name = script_path

            # Absolute path -> relative path
            root = get_script_root().replace("\\", "/")
            self.name = re.sub("^" + re.escape(root) + "/", "", self.name)

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

        # Load cfg
        self.cfg = get_script_config(
            self.real_script_path
            if self.real_script_path is not None
            else self.script_path
        )

        # XXX: Workaround for Mac
        if sys.platform == "darwin":
            self.cfg["newWindow"] = False

    def check_link_existence(self):
        if self.real_script_path is not None:
            if not os.path.exists(self.real_script_path):
                print2("WARNING: cannot locate the link: %s" % self.name)
                # os.remove(self.script_path)
                return False
        return True

    def get_console_title(self):
        return self.console_title if self.console_title else self.name

    def render(self):
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
        template = Script.env.from_string(source)
        ctx = {
            "include": Script.include.__get__(self, Script),
            **self.get_variables(),
        }
        return template.render(ctx)

    def set_override_variables(self, variables):
        self.override_variables = variables

    def get_variables(self):
        if not os.path.isfile(get_variable_file()):
            return {}

        variables = {}
        with open(get_variable_file(), "r") as f:
            variables = json.load(f)

        # Get only last modified value
        variables = {k: (v[0] if len(v) > 0 else "") for k, v in variables.items()}

        # Override variables
        if self.override_variables:
            variables = {**variables, **self.override_variables}

        # Convert into private namespace (shorter variable name)
        prefix = self.get_public_variable_prefix()
        variables = {
            re.sub("^" + re.escape(prefix) + "_", "_", k): v
            for k, v in variables.items()
        }

        # Convert to unix path if on Windows
        if sys.platform == "win32" and self.ext == ".sh":
            variables = {
                k: convert_to_unix_path(v, wsl=self.cfg["wsl"])
                for k, v in variables.items()
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
    ):
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
            # with open(script_path, "r", encoding="utf-8") as f:
            #     set_clip(f.read())
            open_in_vscode(script_path)
            return

        if type(args) == str:
            args = [args]
        elif type(args) == list:
            args = args
        else:
            args = []

        env = {}
        creationflags = 0
        shell = False

        # Install packages
        if self.cfg["packages"] is not None:
            packages = self.cfg["packages"].split()
            for pkg in packages:
                get_executable(pkg)

            if "node" in packages:
                print("node package is required.")
                setup_nodejs(install=False)

        # HACK: pass current folder
        if "_CUR_DIR" in os.environ:
            env["_CUR_DIR"] = os.environ["_CUR_DIR"]

        if cd:
            cwd = os.path.abspath(
                os.path.join(os.getcwd(), os.path.dirname(script_path))
            )
        else:
            cwd = None

        if ext == ".ps1":
            if os.name == "nt":
                if self.cfg["template"]:
                    ps_path = write_temp_file(self.render(), ".ps1")
                else:
                    ps_path = os.path.realpath(script_path)

                args = [
                    "PowerShell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "unrestricted",
                    ps_path,
                ]

        elif ext == ".ahk":
            if os.name == "nt":
                # HACK: add python path to env var
                env["PYTHONPATH"] = os.path.dirname(__file__)

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
                self.cfg["newWindow"] = False

                # Avoid WinError 740: The requested operation requires elevation for AutoHotkeyU64_UIA.exe
                shell = True

        elif ext == ".cmd" or ext == ".bat":
            if os.name == "nt":
                if self.cfg["template"]:
                    batch_file = write_temp_file(self.render(), ".cmd")
                else:
                    batch_file = os.path.realpath(script_path)

                args = ["cmd.exe", "/c", batch_file] + args

                # # HACK: change working directory
                # if platform.system() == 'Windows' and self.cfg['runAsAdmin']:
                #     args = ['cmd', '/c',
                #             'cd', '/d', cwd, '&'] + args
            else:
                print("OS does not support script: %s" % script_path)
                return

        elif ext == ".js":
            # TODO: if self.cfg['template']:
            setup_nodejs()
            args = ["node", script_path] + args

        elif ext == ".sh":
            if self.cfg["template"]:
                bash_cmd = self.render()
            else:
                bash_cmd = _args_to_str(
                    [convert_to_unix_path(script_path, wsl=self.cfg["wsl"])] + args
                )

            args = wrap_bash_commands(bash_cmd, wsl=self.cfg["wsl"], env=env)

        elif ext == ".py" or ext == ".ipynb":
            python_exec = sys.executable

            if self.cfg["template"] and ext == ".py":
                python_file = write_temp_file(self.render(), ".py")
            else:
                python_file = os.path.realpath(script_path)

            if sys.platform == "win32" and self.cfg["wsl"]:
                python_file = convert_to_unix_path(python_file, wsl=self.cfg["wsl"])
                python_exec = "python3"

            setup_python_path(script_path)
            # env["PYTHONDONTWRITEBYTECODE"] = "1"

            # Conda / venv support
            args_activate = []
            if self.cfg["conda"] is not None:
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
                run_py = os.path.abspath(
                    os.path.dirname(__file__) + "/../bin/run_python.py"
                )

                # TODO: make it more general
                if sys.platform == "win32" and self.cfg["wsl"]:
                    run_py = convert_to_unix_path(run_py, wsl=self.cfg["wsl"])

                args = (
                    args_activate
                    + [
                        python_exec,
                        run_py,
                        python_file,
                    ]
                    + args
                )
            elif ext == ".ipynb":
                args = args_activate + ["jupyter", "notebook", python_file] + args

                # HACK: always use new window for jupyter notebook
                self.cfg["newWindow"] = True
            else:
                assert False

            if self.cfg["wsl"]:
                args = wrap_wsl(args)
        elif ext == ".vbs":
            assert os.name == "nt"

            script_abs_path = os.path.join(os.getcwd(), script_path)
            args = ["cscript", "//nologo", script_abs_path] + args

        else:
            print("Not supported script:", ext)

        # Run commands
        if args is not None and len(args) > 0:
            # Check if new window is needed
            if new_window is None:
                new_window = self.cfg["newWindow"]

            if restart_instance is None:
                restart_instance = self.cfg["restartInstance"]

            if restart_instance and new_window:
                # Only works on windows for now
                if platform.system() == "Windows":
                    exec_ahk(
                        "SetTitleMatchMode RegEx\nWinClose, ^"
                        + re.escape(self.get_console_title())
                        + ", , , .*?- Visual Studio Code",
                        wait=True,
                    )

            if new_window:
                # HACK: python wrapper: activate console window once finished
                # TODO: extra console window will be created when runAsAdmin & newWindow
                if sys.platform == "win32" and (not self.cfg["runAsAdmin"]):
                    # TODO: clean up this hack
                    if False and not self.cfg["wsl"]:
                        args = [
                            sys.executable,
                            "-c",
                            (
                                "import subprocess;"
                                "import ctypes;"
                                'import sys;sys.path.append(r"'
                                + os.path.dirname(__file__)
                                + '");'
                                "import _script as s;"
                                's.set_console_title(r"'
                                + self.get_console_title()
                                + '");'
                                "ret = subprocess.call(" + args + ");"
                                "hwnd = ctypes.windll.kernel32.GetConsoleWindow();"
                                "ctypes.windll.user32.SetForegroundWindow(hwnd);"
                                's.set_console_title(s.get_console_title() + " (Finished)");'
                                "sys.exit(ret)"
                            ),
                        ]

                    if self.cfg["terminal"] is None:
                        args = wrap_args_cmd(
                            args,
                            cwd=cwd,
                            title=self.get_console_title(),
                            script_path=script_path,
                            env=env,
                            close_on_exit=close_on_exit,
                        )
                        creationflags = subprocess.CREATE_NEW_CONSOLE
                    else:
                        # Create new terminal using Windows Terminal
                        try:
                            if self.cfg["terminal"] in [
                                "wt",
                                "wsl",
                                "windowsTerminal",
                            ]:
                                args = wt_wrap_args(
                                    args,
                                    cwd=cwd,
                                    title=self.get_console_title(),
                                    wsl=self.cfg["wsl"],
                                    close_on_exit=close_on_exit,
                                )
                            elif self.cfg["terminal"] == "conemu":
                                args = conemu_wrap_args(
                                    args,
                                    cwd=cwd,
                                    title=self.get_console_title(),
                                    wsl=self.cfg["wsl"],
                                    always_on_top=True,
                                )
                            else:
                                raise Exception(
                                    "Non-supported terminal: %s" % self.cfg["terminal"]
                                )
                        except Exception as e:
                            print("Error on Windows Terminal:", e)

                            if os.path.exists(
                                r"C:\Program Files\Git\usr\bin\mintty.exe"
                            ):
                                args = [
                                    r"C:\Program Files\Git\usr\bin\mintty.exe",
                                    "--hold",
                                    "always",
                                ] + args

                elif sys.platform == "linux":
                    args = ["tmux", "split-window"] + args
                    # args = ["x-terminal-emulator", "-e"] + args

                else:
                    creationflags = subprocess.CREATE_NEW_CONSOLE
                    # raise Exception(
                    #     "newWindow flag is not supported on target platform."
                    # )

            # Check if run as admin
            if platform.system() == "Windows" and self.cfg["runAsAdmin"]:
                args = wrap_args_cmd(
                    args,
                    cwd=cwd,
                    title=self.get_console_title(),
                    script_path=script_path,
                    env=env,
                    close_on_exit=close_on_exit,
                )

                print2("Run elevated:")
                print2(_args_to_str(args), color="cyan")
                run_elevated(args, wait=(not new_window))
            else:
                if new_window or self.cfg["background"]:
                    # Check whether or not hide window
                    startupinfo = None
                    if self.cfg["background"]:
                        if platform.system() == "Windows":
                            SW_HIDE = 0
                            startupinfo = subprocess.STARTUPINFO()
                            startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
                            startupinfo.wShowWindow = SW_HIDE
                            creationflags = subprocess.CREATE_NEW_CONSOLE

                    print(_args_to_str(args))
                    subprocess.Popen(
                        args,
                        env={**os.environ, **env},
                        cwd=cwd,
                        startupinfo=startupinfo,
                        creationflags=creationflags,
                        close_fds=True,
                        shell=shell,
                    )
                else:
                    subprocess.check_call(args, env={**os.environ, **env}, cwd=cwd)

    def get_variable_names(self):
        if not self.cfg["template"]:
            return {}

        variables = set()
        include_func = Script.include.__get__(self, Script)

        class MyContext(jinja2.runtime.Context):
            def resolve(self, key):
                if key == "include":
                    return include_func
                variables.add(key)

        Script.env.context_class = MyContext
        self.render()
        Script.env.context_class = jinja2.runtime.Context

        variables = list(variables)

        # Convert private variable to global namespace
        prefix = self.get_public_variable_prefix()
        variables = [prefix + v if v.startswith("_") else v for v in variables]

        return variables

    def include(self, script_name):
        script_path = find_script(script_name, os.path.dirname(self.script_path))
        if script_path is None:
            raise Exception("Cannot find script: %s" % script_name)
        # script_path = os.path.dirname(self.script_path) + '/' + script_path
        return Script(script_path).render()


def find_script(script_name, search_dir=None):
    if script_name.startswith("/"):
        path = os.path.abspath(os.path.dirname(__file__) + "/../scripts" + script_name)
    elif search_dir:
        path = os.path.join(search_dir, script_name)
    else:
        path = os.path.abspath(script_name)

    if os.path.exists(path):
        return path

    # Fuzzy search
    name_no_ext, _ = os.path.splitext(script_name)
    path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "scripts",
            "**",
            name_no_ext + ".*",
        )
    )

    found = glob.glob(path, recursive=True)
    found = [
        f
        for f in found
        if not os.path.isdir(f) and os.path.splitext(f)[1] in SCRIPT_EXTENSIONS
    ]
    if len(found) > 1:
        raise Exception("Found multiple scripts: %s" % str(found))

    return found[0]


def run_script(
    file=None,
    variables=None,
    new_window=False,  # should not start a new window by default
    console_title=None,
    restart_instance=False,
    overwrite_meta=None,
    args=[],
    cd=True,
):
    if file is None:
        if os.path.exists(_get_script_history_file()):
            with open(_get_script_history_file(), "r") as f:
                data = json.load(f)
                file = data["file"]
        else:
            raise ValueError("file cannot be None.")

    # Print command line arguments
    def quote(s):
        if " " in s:
            s = '"%s"' % s
        return s

    print2(
        "run_script: %s" % (" ".join([quote(x) for x in [file] + args])), color="black"
    )

    script_path = find_script(file)
    if script_path is None:
        raise Exception('[ERROR] Cannot find script: "%s"' % file)

    script = Script(script_path)

    if console_title:
        script.console_title = console_title

    if overwrite_meta:
        for k, v in overwrite_meta.items():
            script.cfg[k] = v

    # Set console window title (for windows only)
    if console_title and platform.system() == "Windows":
        # Save previous title
        MAX_BUFFER = 260
        saved_title = (ctypes.c_char * MAX_BUFFER)()
        res = ctypes.windll.kernel32.GetConsoleTitleA(saved_title, MAX_BUFFER)
        win_title = console_title.encode(locale.getpreferredencoding())
        ctypes.windll.kernel32.SetConsoleTitleA(win_title)

    if variables:
        script.set_override_variables(variables)

    script.execute(
        restart_instance=restart_instance,
        new_window=new_window,
        args=args,
        cd=cd,
    )
    if script.return_code != 0:
        raise Exception("[ERROR] %s returns %d" % (file, script.return_code))

    # Restore title
    if console_title and platform.system() == "Windows":
        ctypes.windll.kernel32.SetConsoleTitleA(saved_title)


def get_script_default_config():
    return {
        "template": True,
        "hotkey": None,
        "globalHotkey": None,
        "alias": None,
        "newWindow": True,
        "runAsAdmin": False,
        "autoRun": False,
        "wsl": False,
        "conda": None,
        "restartInstance": True,
        "background": False,
        "venv": None,
        "closeOnExit": True,
        "terminal": None,
        "packages": None,
    }


def load_script_config(script_config_file):
    return yaml.load(open(script_config_file, "r").read(), Loader=yaml.FullLoader)


def save_script_config(data, script_config_file):
    yaml.dump(data, open(script_config_file, "w", newline="\n"), default_flow_style=False)


def get_default_script_config_file(script_path):
    return os.path.splitext(script_path)[0] + ".config.yaml"


def get_script_config_file(script_path):
    f = get_default_script_config_file(script_path)
    if os.path.exists(f):
        return f

    f = os.path.join(os.path.dirname(script_path), "default.yaml")
    if os.path.exists(f):
        return f

    return None


def get_script_config(script_path):
    script_meta_file = get_script_config_file(script_path)
    if script_meta_file:
        data = load_script_config(script_meta_file)
    else:
        data = None

    config = get_script_default_config()

    # override default config
    if data is not None:
        for k, v in data.items():
            config[k] = v

    return config


def create_script_link(script_file):
    script_dir = os.path.realpath(os.path.dirname(__file__) + "/../scripts")
    link_file = os.path.splitext(os.path.basename(script_file))[0] + ".link"
    link_file = os.path.join(script_dir, link_file)
    with open(link_file, "w", encoding="utf-8") as f:
        f.write(script_file)
    print("Link created: %s" % link_file)


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


def update_script_acesss_time(script):
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


def _replace_prefix(text, prefix, repl=""):
    if text.startswith(prefix):
        return repl + text[len(prefix) :]
    return text  # or whatever


def get_scripts_recursive(directory):
    for root, dirs, files in os.walk(directory, topdown=True):
        dirs[:] = [
            d
            for d in dirs
            if not d.startswith("_")  # Ignore folder if startswith `_`
            and not os.path.exists(
                os.path.join(root, d + ".ignore")
            )  # Ignore folder if `<folder>.ignore` exists
        ]

        for f in files:
            ext = os.path.splitext(f)[1].lower()

            # Filter by script extensions
            if ext in SCRIPT_EXTENSIONS:
                yield os.path.join(root, f)


def script_updated():
    if not hasattr(script_updated, "last_mtime"):
        script_updated.last_mtime = 0
        script_updated.file_list = None

    mtime = 0
    file_list = []
    for _, d in get_script_directories():
        for f in get_scripts_recursive(d):
            mtime = max(mtime, os.path.getmtime(f))
            script_config_file = get_script_config_file(f)
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


def load_scripts(script_list, modified_time, autorun=True):
    if not script_updated():
        return False

    # TODO: only update modified scripts
    script_list.clear()

    for prefix, script_path in get_script_directories():
        files = get_scripts_recursive(script_path)
        for file in files:
            # File has been removed during iteration
            if not os.path.exists(file):
                continue

            mtime = os.path.getmtime(file)
            script_config_file = get_script_config_file(file)
            if script_config_file:
                mtime = max(mtime, os.path.getmtime(script_config_file))

            # Initialize script name
            name = _replace_prefix(file, script_path, prefix)
            name, ext = os.path.splitext(name)  # Remove ext
            name = name.replace("\\", "/")
            name = _replace_prefix(name, "/", "")

            script = Script(file, name=name)

            if file not in modified_time or mtime > modified_time[file]:
                # Check if auto run script
                if script.cfg["autoRun"] and autorun:
                    print2("AUTORUN: ", end="", color="cyan")
                    print(file)
                    script.execute(new_window=False)

            # Hide files starting with '_'
            base_name = os.path.basename(file)
            if not base_name.startswith("_"):
                script_list.append(script)

            modified_time[file] = mtime

    return True
