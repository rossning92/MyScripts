import os
import sys
import subprocess
import json
import jinja2
import re
import yaml
import platform
import ctypes
from _shutil import *
import shlex
import glob
import locale
from _appmanager import get_executable
from _editor import open_in_vscode

# TODO: move to configuration file
SCRIPT_PATH_LIST = [
    ["", os.path.abspath(os.path.dirname(__file__) + "/../scripts")],
    ["gdrive", expandvars(r"%USERPROFILE%\Google Drive\Scripts")],
]

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

    return ["bash", tmp_sh_file]


def wrap_bash_commands(commands, wsl=False, env=None):
    assert type(commands) == str

    if os.name == "nt" and wsl:  # WSL (Windows Subsystem for Linux)
        return wrap_wsl(commands)

    elif os.name == "nt":
        if env is not None:
            env["MSYS_NO_PATHCONV"] = "1"  # Disable path conversion

        tmp_sh_file = write_temp_file(commands, ".sh")
        return [r"C:\Program Files\Git\bin\bash.exe", "--login", "-i", tmp_sh_file]

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


def get_data_folder():
    app_dir = os.path.abspath(os.path.dirname(__file__) + "/../")
    folder = os.path.join(app_dir, "data", platform.node())
    os.makedirs(folder, exist_ok=True)
    return folder


def get_variable_file():
    variable_file = os.path.join(get_data_folder(), "variables.json")
    return variable_file


def get_all_variables():
    with open(get_variable_file(), "r") as f:
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
    with open(get_variable_file(), "r") as f:
        variables = json.load(f)

    if name not in variables:
        return None

    return variables[name][-1]


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
    vals.append(val)

    with open(file, "w") as f:
        json.dump(variables, f, indent=4)


def get_python_path(script_path):
    python_path = []

    if True:  # Add path directories to python path
        script_root_path = os.path.dirname(__file__) + "/../scripts"
        script_root_path = os.path.abspath(script_root_path)
        script_full_path = os.path.join(os.getcwd(), script_path)
        parent_dir = os.path.dirname(script_full_path)
        python_path.append(parent_dir)
        while True:
            parent_dir = os.path.abspath(parent_dir + "/../")
            if parent_dir.startswith(script_root_path):
                python_path.append(parent_dir)
            else:
                break

    python_path.append(os.path.dirname(__file__))
    return python_path


def wt_wrap_args(args, wsl=False, title=None, close_on_exit=True, cwd=None):
    THEME = {
        "name": "Dracula",
        "background": "#282A36",
        "black": "#21222C",
        "blue": "#BD93F9",
        "brightBlack": "#6272A4",
        "brightBlue": "#D6ACFF",
        "brightCyan": "#A4FFFF",
        "brightGreen": "#69FF94",
        "brightPurple": "#FF92DF",
        "brightRed": "#FF6E6E",
        "brightWhite": "#FFFFFF",
        "brightYellow": "#FFFFA5",
        "cyan": "#8BE9FD",
        "foreground": "#F8F8F2",
        "green": "#50FA7B",
        "purple": "#FF79C6",
        "red": "#FF5555",
        "white": "#F8F8F2",
        "yellow": "#F1FA8C",
    }

    if sys.platform != "win32":
        raise Exception("the function can only be called on windows platform.")

    CONFIG_FILE = os.path.expandvars(
        r"%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"
    )

    with open(CONFIG_FILE, "r") as f:
        lines = f.read().splitlines()

    lines = [x for x in lines if not x.lstrip().startswith("//")]
    data = json.loads("\n".join(lines))

    data["profiles"]["defaults"]["colorScheme"] = "Dracula"
    # data["profiles"]["defaults"]["fontSize"] = 12
    data["schemes"] = [THEME]

    if title:
        filtered = list(filter(lambda x: x["name"] == title, data["profiles"]["list"]))
        profile = {
            "name": title,
            "hidden": False,
            "commandline": "wsl -d Ubuntu" if wsl else "cmd.exe",
            "closeOnExit": "graceful" if close_on_exit else "never",
            "suppressApplicationTitle": True,
        }
        if len(filtered) == 0:
            data["profiles"]["list"].append(profile)
        else:
            filtered[0].update(profile)

    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

    return ["wt", "-p", title] + args


class ScriptItem:
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath="./"))

    def __str__(self):
        result = self.name

        if self.ext == ".link":
            result += " [lnk]"

        # Name: show shortcut
        if self.meta["hotkey"]:
            result += "  (%s)" % self.meta["hotkey"].lower().replace(
                "win+", "#"
            ).replace("ctrl+", "^").replace("alt+", "!").replace("shift+", "+")

        if self.meta["globalHotkey"]:
            result += "  (%s)" % self.meta["globalHotkey"].lower().replace(
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

        self.meta = get_script_meta(script_path)  # Load meta
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

        # XXX: Workaround for mac
        if sys.platform == "darwin":
            self.meta["newWindow"] = False

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
        template = ScriptItem.env.from_string(source)
        ctx = {
            "include": ScriptItem.include.__get__(self, ScriptItem),
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
        variables = {k: (v[-1] if len(v) > 0 else "") for k, v in variables.items()}

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
                k: convert_to_unix_path(v, wsl=self.meta["wsl"])
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
        self, args=None, new_window=None, restart_instance=None, close_on_exit=None
    ):
        script_path = (
            self.real_script_path if self.real_script_path else self.script_path
        )
        ext = self.real_ext if self.real_ext else self.ext

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
        if self.meta["packages"] is not None:
            packages = self.meta["packages"].split()
            for pkg in packages:
                get_executable(pkg)

            if "node" in packages:
                print("node package is required.")
                setup_nodejs(install=False)

        # HACK: pass current folder
        if "CURRENT_FOLDER" in os.environ:
            env["CURRENT_FOLDER"] = os.environ["CURRENT_FOLDER"]

        cwd = os.path.abspath(os.path.join(os.getcwd(), os.path.dirname(script_path)))

        if ext == ".ps1":
            if os.name == "nt":
                if self.meta["template"]:
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

                if self.meta["template"]:
                    script_path = write_temp_file(
                        self.render(),
                        os.path.join(
                            "GeneratedAhkScript/", os.path.basename(self.script_path)
                        ),
                    )
                else:
                    script_path = os.path.abspath(script_path)

                args = [get_ahk_exe(), script_path]

                self.meta["background"] = True

                if self.meta["runAsAdmin"]:
                    args = ["start"] + args

                # Disable console window for ahk
                self.meta["newWindow"] = False

                # Avoid WinError 740: The requested operation requires elevation for AutoHotkeyU64_UIA.exe
                shell = True

        elif ext == ".cmd" or ext == ".bat":
            if os.name == "nt":
                if self.meta["template"]:
                    batch_file = write_temp_file(self.render(), ".cmd")
                else:
                    batch_file = os.path.realpath(script_path)

                args = ["cmd.exe", "/c", batch_file] + args

                # # HACK: change working directory
                # if platform.system() == 'Windows' and self.meta['runAsAdmin']:
                #     args = ['cmd', '/c',
                #             'cd', '/d', cwd, '&'] + args
            else:
                print("OS does not support script: %s" % script_path)
                return

        elif ext == ".js":
            # TODO: if self.meta['template']:
            setup_nodejs()
            args = ["node", os.path.basename(script_path)]

        elif ext == ".sh":
            if self.meta["template"]:
                bash_cmd = self.render()
            else:
                bash_cmd = _args_to_str(
                    [convert_to_unix_path(script_path, wsl=self.meta["wsl"])] + args
                )

            args = wrap_bash_commands(bash_cmd, wsl=self.meta["wsl"], env=env)

        elif ext == ".py" or ext == ".ipynb":
            python_exec = sys.executable

            if self.meta["template"] and ext == ".py":
                python_file = write_temp_file(self.render(), ".py")
            else:
                python_file = os.path.realpath(script_path)

            if sys.platform == "win32" and self.meta["wsl"]:
                python_file = convert_to_unix_path(python_file, wsl=self.meta["wsl"])
                python_exec = "python3"

            python_path = get_python_path(script_path)

            env["PYTHONPATH"] = os.pathsep.join(python_path)
            env["PYTHONDONTWRITEBYTECODE"] = "1"

            # Conda / venv support
            args_activate = []
            if self.meta["conda"] is not None:
                assert sys.platform == "win32"
                import _conda

                env_name = self.meta["conda"]
                conda_path = _conda.get_conda_path()

                activate = conda_path + "\\Scripts\\activate.bat"

                if env_name != "base" and not exists(
                    conda_path + "\\envs\\" + env_name
                ):
                    call_echo(
                        'call "%s" & conda create --name %s python=3.6'
                        % (activate, env_name)
                    )

                args_activate = ["cmd", "/c", "call", activate, env_name, "&"]

            elif self.meta["venv"]:
                assert sys.platform == "win32"
                venv_path = os.path.expanduser("~\\venv\\%s" % self.meta["venv"])
                if not exists(venv_path):
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
                if sys.platform == "win32" and self.meta["wsl"]:
                    run_py = convert_to_unix_path(run_py, wsl=self.meta["wsl"])

                args = args_activate + [python_exec, run_py, python_file,] + args
            elif ext == ".ipynb":
                args = args_activate + ["jupyter", "notebook", python_file] + args

                # HACK: always use new window for jupyter notebook
                self.meta["newWindow"] = True
            else:
                assert False

            if self.meta["wsl"]:
                args = wrap_wsl(args)

        elif ext == ".vbs":
            assert os.name == "nt"

            script_abs_path = os.path.join(os.getcwd(), script_path)
            args = ["cscript", "//nologo", script_abs_path]

        else:
            print("Not supported script:", ext)

        # Run commands
        if args is not None and len(args) > 0:
            # Check if new window is needed
            if new_window is None:
                new_window = self.meta["newWindow"]

            if restart_instance is None:
                restart_instance = self.meta["restartInstance"]

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
                if sys.platform == "win32" and (not self.meta["runAsAdmin"]):
                    # TODO:
                    if not self.meta["wsl"] and False:
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

                    # Create new terminal using Windows Terminal
                    try:
                        if self.meta["terminal"] is None:
                            args = wt_wrap_args(
                                args,
                                cwd=cwd,
                                title=self.get_console_title(),
                                wsl=self.meta["wsl"],
                                close_on_exit=(
                                    close_on_exit
                                    if close_on_exit is not None
                                    else self.meta["closeOnExit"]
                                ),
                            )
                        elif self.meta["terminal"] == "conemu":
                            args = conemu_wrap_args(
                                args,
                                cwd=cwd,
                                title=self.get_console_title(),
                                wsl=self.meta["wsl"],
                            )
                        else:
                            raise Exception(
                                "Non-supported terminal: %s" % self.meta["terminal"]
                            )
                    except Exception as e:
                        print("Error on Windows Terminal:", e)

                        if os.path.exists(r"C:\Program Files\Git\usr\bin\mintty.exe"):
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
            if platform.system() == "Windows" and self.meta["runAsAdmin"]:
                # Set environment variables through command lines
                bin_path = os.path.abspath(os.path.dirname(__file__) + "/../bin")
                set_env_var = []
                for k, v in env.items():
                    set_env_var += ["set", "%s=%s" % (k, v), "&"]

                args = (
                    ["cmd", "/c"]
                    + (
                        ["title", self.get_console_title(), "&"]
                        if ext != ".ahk"
                        else []
                    )
                    + ["cd", "/d", cwd, "&"]
                    + ["set", "PATH=" + bin_path + ";%PATH%", "&"]
                    + set_env_var
                    + args
                )

                print2("Run elevated:")
                print2(_args_to_str(args), color="cyan")
                run_elevated(args, wait=(not new_window))
            else:
                if new_window or self.meta["background"]:
                    # Check whether or not hide window
                    startupinfo = None
                    if self.meta["background"]:
                        if platform.system() == "Windows":
                            SW_HIDE = 0
                            startupinfo = subprocess.STARTUPINFO()
                            startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
                            startupinfo.wShowWindow = SW_HIDE
                            creationflags = subprocess.CREATE_NEW_CONSOLE

                    print(args)
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
        variables = set()
        include_func = ScriptItem.include.__get__(self, ScriptItem)

        class MyContext(jinja2.runtime.Context):
            def resolve(self, key):
                if key == "include":
                    return include_func
                variables.add(key)

        ScriptItem.env.context_class = MyContext
        self.render()
        ScriptItem.env.context_class = jinja2.runtime.Context

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
        return ScriptItem(script_path).render()


def get_script_root():
    return os.path.abspath(os.path.dirname(__file__) + "/../scripts")


def find_script(script_name, search_dir=None):
    if script_name.startswith("/"):
        script_path = os.path.abspath(
            os.path.dirname(__file__) + "/../scripts" + script_name
        )
    elif search_dir:
        script_path = os.path.join(search_dir, script_name)
    else:
        script_path = os.path.abspath(script_name)

    if os.path.exists(script_path):
        return script_path

    for f in glob.glob(script_path + "*"):
        if os.path.isdir(f):
            continue
        if os.path.splitext(f)[1] == ".yaml":
            continue
        return f

    return None


def run_script(
    script_name,
    variables=None,
    new_window=False,
    console_title=None,
    restart_instance=False,
    overwrite_meta=None,
):
    print2("RunScript: %s" % script_name, color="green")
    script_path = find_script(script_name)
    if script_path is None:
        raise Exception('[ERROR] Cannot find script: "%s"' % script_name)

    script = ScriptItem(script_path)

    if console_title:
        script.console_title = console_title

    if overwrite_meta:
        for k, v in overwrite_meta.items():
            script.meta[k] = v

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

    script.execute(restart_instance=restart_instance, new_window=new_window)
    if script.return_code != 0:
        raise Exception("[ERROR] %s returns %d" % (script_name, script.return_code))

    # Restore title
    if console_title and platform.system() == "Windows":
        ctypes.windll.kernel32.SetConsoleTitleA(saved_title)


def get_default_meta():
    return {
        "template": True,
        "hotkey": None,
        "globalHotkey": None,
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


def load_meta_file(meta_file):
    return yaml.load(open(meta_file, "r").read(), Loader=yaml.FullLoader)


def save_meta_file(data, meta_file):
    yaml.dump(data, open(meta_file, "w", newline="\n"), default_flow_style=False)


def get_script_config_file(script_path):
    script_meta_file = os.path.splitext(script_path)[0] + ".yaml"
    return script_meta_file if os.path.exists(script_meta_file) else None


def get_script_meta(script_path):
    script_meta_file = os.path.splitext(script_path)[0] + ".yaml"
    default_meta_file = os.path.join(os.path.dirname(script_path), "default.yaml")

    meta = get_default_meta()

    data = None
    if os.path.exists(script_meta_file):
        data = load_meta_file(script_meta_file)

    elif os.path.exists(default_meta_file):
        data = load_meta_file(default_meta_file)

    # override default config
    if data is not None:
        for k, v in data.items():
            meta[k] = v

    return meta


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
    data_path = os.path.abspath(
        os.path.dirname(__file__) + "/../data/" + platform.node()
    )
    config_file = os.path.join(data_path, "script_access_time.json")
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
        dirs[:] = [d for d in dirs if not d.startswith("_")]
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
    for _, d in SCRIPT_PATH_LIST:
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

    for prefix, script_path in SCRIPT_PATH_LIST:
        files = get_scripts_recursive(script_path)
        for file in files:
            ext = os.path.splitext(file)[1].lower()

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

            script = ScriptItem(file, name=name)

            if file not in modified_time or mtime > modified_time[file]:
                # Check if auto run script
                if script.meta["autoRun"] and autorun:
                    print2("AUTORUN: ", end="", color="cyan")
                    print(file)
                    script.execute(new_window=False)

            # Hide files starting with '_'
            base_name = os.path.basename(file)
            if not base_name.startswith("_"):
                script_list.append(script)

            modified_time[file] = mtime

    return True

