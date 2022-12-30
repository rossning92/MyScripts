import argparse
import curses
import logging
import os
import shutil
import subprocess
import sys
import time
import traceback
from typing import Callable, Dict, List

SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(SCRIPT_ROOT, "libs"))
sys.path.append(os.path.join(SCRIPT_ROOT, "bin"))


from _ext import (
    copy_script_path_to_clipboard,
    create_new_script,
    edit_myscript_script,
    edit_script_config,
    rename_script,
)
from _script import (
    Script,
    get_all_script_access_time,
    get_all_variables,
    get_data_dir,
    get_script_variables,
    is_instance_running,
    reload_scripts,
    save_variables,
    setup_env_var,
    update_script_access_time,
)
from _shutil import (
    append_to_path_global,
    get_ahk_exe,
    getch,
    quote_arg,
    refresh_env_vars,
    run_at_startup,
    setup_logger,
    setup_nodejs,
    start_process,
    update_env_var_explorer,
)
from _template import render_template_file
from _term import Menu

REFRESH_INTERVAL_SECS = 60
GLOBAL_HOTKEY = os.path.join(get_data_dir(), "GlobalHotkey.ahk")
KEY_CODE_CTRL_ENTER_WIN = 529


callback_queue = []


def execute_script(script: Script, close_on_exit=None, new_window=None):
    refresh_env_vars()
    args = update_env_var_explorer()
    success = script.execute(
        args=args,
        close_on_exit=close_on_exit,
        restart_instance=True,
        new_window=new_window,
    )
    if not success:
        print("(press any key to continue...)")
        getch()


def setup_console_font():
    import ctypes

    LF_FACESIZE = 32
    STD_OUTPUT_HANDLE = -11

    class COORD(ctypes.Structure):
        _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

    class CONSOLE_FONT_INFOEX(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.c_ulong),
            ("nFont", ctypes.c_ulong),
            ("dwFontSize", COORD),
            ("FontFamily", ctypes.c_uint),
            ("FontWeight", ctypes.c_uint),
            ("FaceName", ctypes.c_wchar * LF_FACESIZE),
        ]

    font = CONSOLE_FONT_INFOEX()
    font.cbSize = ctypes.sizeof(CONSOLE_FONT_INFOEX)
    font.nFont = 12
    font.dwFontSize.X = 11
    font.dwFontSize.Y = 18
    font.FontFamily = 54
    font.FontWeight = 400
    font.FaceName = "Lucida Console"

    handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    ctypes.windll.kernel32.SetCurrentConsoleFontEx(
        handle, ctypes.c_long(False), ctypes.pointer(font)
    )


def to_ascii_hotkey(hotkey: str):
    hotkey = hotkey.lower()
    key = hotkey[-1].lower()
    if "ctrl+" in hotkey:
        ch = curses.ascii.ctrl(ord(key))
    elif "shift+" in hotkey or "alt+" in hotkey:
        # HACK: use `shift+` in place of `alt+`
        ch = ord(key.upper())
    else:
        ch = ord(key)
    return ch


def register_hotkeys(scripts) -> Dict[str, Script]:
    hotkeys = {}
    for script in scripts:
        hotkey = script.cfg["hotkey"]
        if hotkey:
            logging.debug("Hotkey: %s: %s" % (hotkey, script.name))
            ch = to_ascii_hotkey(hotkey)
            hotkeys[ch] = script

    return hotkeys


class VariableEditWindow(Menu):
    def __init__(self, vars, var_name):
        self.vars = vars
        self.var_name = var_name

        super().__init__(
            items=self.vars[var_name] if var_name in self.vars else [],
            label=var_name,
            text="",
        )

    def save_variable_val(self, val):
        if self.var_name not in self.vars:
            self.vars[self.var_name] = []
        try:
            self.vars[self.var_name].remove(val)
        except ValueError:
            pass
        self.vars[self.var_name].insert(0, val)

        save_variables(self.vars)

    def on_enter_pressed(self):
        self.save_variable_val(self.get_text())
        self.close()

    def on_char(self, ch):
        if ch == ord("\t"):
            val = self.get_selected_text()
            if val is not None:
                self.input_.set_text(val)
            return True

        return False


def get_variable_str_list(vars, var_names):
    result = []
    var_name_length = [len(val_name) for val_name in var_names]
    if var_name_length:
        max_width = max(var_name_length) + 1
    else:
        max_width = 0
    for var_name in var_names:
        var_val = (
            vars[var_name][0] if (var_name in vars and len(vars[var_name]) > 0) else ""
        )
        result.append(var_name.ljust(max_width) + ": " + var_val)
    return result


class VariableWindow(Menu):
    def __init__(self, script):
        super().__init__(label="edit params")
        self.vars = get_all_variables()
        self.var_names = sorted(script.get_variable_names())
        self.enter_pressed = False

        if len(self.var_names) > 0:
            self.update_items()

    def update_items(self):
        self.items[:] = get_variable_str_list(self.vars, self.var_names)

    def on_enter_pressed(self):
        self.enter_pressed = True
        self.close()

    def on_char(self, ch):
        if ch == ord("\t"):
            self.edit_variable()
            return True
        return False

    def edit_variable(self):
        index = self.get_selected_index()
        var_name = self.var_names[index]
        VariableEditWindow(self.vars, var_name).exec()
        self.update_items()
        self.input_.clear()


class ScriptManager:
    def __init__(self, autorun=True):
        self.scripts: List[Script] = []
        self.last_refresh_time = 0
        self.hotkeys = {}
        self.autorun = autorun

    def update_access_time(self):
        access_time, _ = get_all_script_access_time()
        for script in self.scripts:
            if script.script_path in access_time:
                script.mtime = max(
                    script.mtime,
                    access_time[script.script_path],
                )

    def sort_scripts(self):
        self.update_access_time()
        self.scripts[:] = sorted(
            self.scripts,
            key=lambda script: script.mtime,
            reverse=True,
        )

    def refresh_all_scripts(self):
        begin_time = time.time()

        if reload_scripts(self.scripts, autorun=self.autorun, startup=args.startup):
            self.hotkeys = register_hotkeys(self.scripts)
            register_global_hotkeys(self.scripts)
        self.sort_scripts()
        self.last_refresh_time = time.time()

        logging.info(
            "Script reloading takes %.1f secs." % (self.last_refresh_time - begin_time)
        )


def add_keyboard_hooks(keyboard_hooks):
    if sys.platform != "linux":
        import keyboard

        keyboard.unhook_all()
        for hotkey, func in keyboard_hooks.items():
            keyboard.add_hotkey(hotkey, func)


def register_global_hotkeys_linux(scripts):
    if not shutil.which("sxhkd"):
        logging.warning("sxhkd is not installed, skip global hotkey registration.")
        return

    s = (
        f"control+q\n"
        # f"  x-terminal-emulator -e python3 {SCRIPT_ROOT}/run.py -q\n"
        "  wmctrl -a MyScriptsTerminal\n"
        "\n"
    )

    for item in scripts:
        hotkey = item.cfg["globalHotkey"]

        if hotkey:
            hotkey = (
                hotkey.lower()
                .replace("win+", "super+")
                .replace("enter", "Return")
                .replace("[", "bracketleft")
                .replace("]", "bracketright")
            )
            s += "{}\n".format(hotkey)
            s += f"  python3 {SCRIPT_ROOT}/bin/start_script.py {item.script_path}\n\n"

    with open(os.path.expanduser("~/.sxhkdrc"), "w") as f:
        f.write(s)
    subprocess.call(["pkill", "-USR1", "sxhkd"])
    start_process(["sxhkd", "-c", os.path.expanduser("~/.sxhkdrc")])


def register_global_hotkeys_win(scripts):
    hotkeys = ""
    match_clipboard = []

    for item in scripts:
        hotkey = item.cfg["globalHotkey"]
        if hotkey:
            if hotkey:
                hotkey = hotkey.lower()
                hotkey = hotkey.replace("ctrl+", "^")
                hotkey = hotkey.replace("alt+", "!")
                hotkey = hotkey.replace("shift+", "+")
                hotkey = hotkey.replace("win+", "#")
                hotkeys += f'{hotkey}::RunScript("{item.name}", "{item.script_path}")\n'
        mc = item.cfg["matchClipboard"]
        if mc:
            match_clipboard.append([mc, item.name, item.script_path])

    render_template_file(
        "GlobalHotkey.ahk",
        GLOBAL_HOTKEY,
        context={
            "PYTHON_EXEC": sys.executable,
            "START_SCRIPT": os.path.abspath("bin/start_script.py"),
            "RUN_SCRIPT": os.path.abspath("bin/run_script.py"),
            "HOTKEYS": hotkeys,
            "MATCH_CLIPBOARD": str(match_clipboard)
            .replace("\\\\", "\\")
            .replace("'", '"'),
        },
    )

    subprocess.Popen([get_ahk_exe(), GLOBAL_HOTKEY], close_fds=True, shell=True)


def register_global_hotkeys_mac(scripts):
    keyboard_hooks = {}
    for script in scripts:
        hotkey = script.cfg["globalHotkey"]
        if hotkey:
            logging.info("GlobalHotkey: %s: %s" % (hotkey, script.name))
            keyboard_hooks[hotkey] = lambda script=script: execute_script(script)
    add_keyboard_hooks(keyboard_hooks)


def register_global_hotkeys(scripts):
    if sys.platform == "win32":
        register_global_hotkeys_win(scripts)
    elif sys.platform == "linux":
        register_global_hotkeys_linux(scripts)
    elif sys.platform == "darwin":
        register_global_hotkeys_mac(scripts)


class InternalHotkey:
    def __init__(self, hotkey: str, func: Callable):
        self.hotkey = hotkey
        self.func = func

    def __str__(self) -> str:
        return "%s  (%s)" % (self.func.__name__, self.hotkey)


def restart_program():
    os.execl(
        sys.executable,
        sys.executable,
        *(x for x in sys.argv if x != "--startup"),
    )


class MainWindow(Menu):
    def __init__(self, new_window=None):
        self.new_window = new_window

        super().__init__(
            items=script_manager.scripts,
            ascii_only=True,
            cancellable=False,
        )

        self.internal_hotkeys: Dict[str, InternalHotkey] = {}
        self.add_internal_hotkey("ctrl+r", self._reload_script)
        self.add_internal_hotkey("shift+m", self._edit_script_config)
        self.add_internal_hotkey("shift+c", self._copy_to_clipboard)
        self.add_internal_hotkey("ctrl+n", self._new_script)
        self.add_internal_hotkey("ctrl+d", self._duplicate_script)
        self.add_internal_hotkey("shift+n", self._rename_script)
        self.add_internal_hotkey("ctrl+e", self._edit_script)
        self.add_internal_hotkey("?", self._help)

    def add_internal_hotkey(self, hotkey, func):
        ch = to_ascii_hotkey(hotkey)
        self.internal_hotkeys[ch] = InternalHotkey(hotkey=hotkey, func=func)

    def on_main_loop(self):
        # Reload scripts
        now = time.time()
        if (
            now - self.last_key_pressed_timestamp > REFRESH_INTERVAL_SECS
            and now - script_manager.last_refresh_time > REFRESH_INTERVAL_SECS
        ):
            self.set_message("(reloading scripts...)")
            script_manager.refresh_all_scripts()
            self.set_message(None)

    def run_selected_script(self, close_on_exit=None):
        index = self.get_selected_index()
        if index >= 0:
            script = self.items[index]

            update_script_access_time(script)
            script_manager.sort_scripts()

            callback_queue.append(
                lambda: execute_script(
                    script,
                    close_on_exit=close_on_exit,
                    new_window=self.new_window,
                )
            )
            self.close()

    def get_selected_script_path(self):
        index = self.get_selected_index()
        if index >= 0:
            return self.items[index].script_path

    def _reload_script(self):
        self.set_message("(reloading scripts...)")
        script_manager.refresh_all_scripts()
        self.set_message(None)
        return True

    def _edit_script_config(self):
        script_path = self.get_selected_script_path()
        if script_path:
            edit_script_config(script_path)
            # reload the current script
            index = self.get_selected_index()
            self.items[index] = Script(script_path)
            self.input_.clear()

    def _copy_to_clipboard(self):
        script_path = self.get_selected_script_path()
        if script_path:
            content = copy_script_path_to_clipboard(script_path)
            self.set_message(
                f"(copied to clipboard: {content})"
                if content
                else "Copied to clipboard."
            )
            self.input_.clear()

    def _new_script_or_duplicate_script(self, duplicate=False):
        ref_script_path = self.get_selected_script_path()
        if ref_script_path:
            script_path = create_new_script(
                ref_script_path=ref_script_path, duplicate=duplicate
            )
            if script_path:
                script = Script(script_path)
                script_manager.scripts.insert(0, script)
        self.input_.clear()

    def _new_script(self):
        self._new_script_or_duplicate_script(duplicate=False)

    def _duplicate_script(self):
        self._new_script_or_duplicate_script(duplicate=True)

    def _rename_script(self):
        script_path = self.get_selected_script_path()
        if script_path:
            self.set_message("(searching scripts to rename...)")
            script_manager.refresh_all_scripts()
            if rename_script(script_path):
                script_manager.refresh_all_scripts()
            self.set_message(None)
        self.input_.clear()

    def _edit_script(self):
        script_path = self.get_selected_script_path()
        if script_path:
            callback_queue.append(lambda: edit_myscript_script(script_path))
            self.close()

    def _help(self):
        items = []
        items.extend(self.internal_hotkeys.values())
        items.extend(script_manager.hotkeys.values())
        w = Menu(label="all hotkeys", items=items)
        w.exec()

    def on_char(self, ch):
        self.last_refresh_time = time.time()

        if ch in self.internal_hotkeys:
            self.internal_hotkeys[ch].func()
            return True

        elif ch == ord("\n"):
            self.run_selected_script()
            return True

        elif ch == curses.ascii.ctrl(ord("c")):
            sys.exit(0)

        elif ch == KEY_CODE_CTRL_ENTER_WIN:
            self.run_selected_script(close_on_exit=False)
            return True

        elif ch == ord("\t"):
            script = self.get_selected_text()
            if script is not None:
                w = VariableWindow(script)
                if w.var_names:
                    w.exec()
                    if w.enter_pressed:
                        self.run_selected_script()
            return True

        elif ch == ord("L"):
            callback_queue.append(lambda: restart_program())
            self.close()

        elif ch in script_manager.hotkeys:
            script = self.get_selected_text()
            if script is not None:
                script_abs_path = os.path.abspath(script.script_path)
                os.environ["SCRIPT"] = script_abs_path

                callback_queue.append(
                    lambda: execute_script(script_manager.hotkeys[ch])
                )
                callback_queue.append(lambda: script_manager.sort_scripts())
                self.close()
                return True

        self.set_message(None)
        return False

    def on_update_screen(self):
        height = self.height

        try:
            script = self.get_selected_text()
            if script is not None:
                vars = get_script_variables(script)
                if len(vars):
                    str_list = get_variable_str_list(
                        vars, sorted(script.get_variable_names())
                    )
                    height = max(5, height - len(vars))
                    for i, s in enumerate(str_list):
                        if height + i >= self.height:
                            break
                        try:
                            Menu.stdscr.addstr(height + i, 0, s)
                        except:
                            pass

        except FileNotFoundError:  # Scripts have been removed
            pass

        super().on_update_screen(max_height=height)


def init(autorun=True):
    setup_logger(
        log_file=os.path.join(get_data_dir(), "MyScripts.log"),
        stdout=False,
        level=logging.INFO,
    )

    logging.info("Python executable: %s" % sys.executable)

    # Add bin folder to PATH
    bin_dir = os.path.join(SCRIPT_ROOT, "bin")
    append_to_path_global(bin_dir)

    user_site = subprocess.check_output(
        [sys.executable, "-m", "site", "--user-site"], universal_newlines=True
    ).strip()
    script_dir = os.path.abspath(os.path.join(user_site, "..", "Scripts"))
    append_to_path_global(script_dir)

    setup_env_var(os.environ)

    refresh_env_vars()

    setup_nodejs(install=False)

    if autorun and is_instance_running():
        logging.info("An instance is already running, exiting.")
        sys.exit(0)


def main_loop(new_window=None, quit=False):
    while True:
        try:
            MainWindow(new_window=new_window).exec()

            while len(callback_queue) > 0:
                callback = callback_queue.pop(0)
                callback()

            if quit:
                break

            # HACK: workaround: key bindings will not work on windows.
            # time.sleep(1)

        except Exception:
            traceback.print_exc(file=sys.stdout)
            input("Press any key to retry...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-q",
        "--quit",
        action="store_true",
        help="quit after running a script",
    )
    parser.add_argument(
        "-n",
        "--no-gui",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--startup",
        action="store_true",
        help="will autorun all scripts with runAtStartup=True",
    )
    args = parser.parse_args()

    run_at_startup(
        name="MyScripts",
        cmdline=quote_arg(os.path.join(SCRIPT_ROOT, "run.cmd")) + " --startup",
    )

    # setup_console_font()
    init(autorun=not args.no_gui)
    script_manager = ScriptManager(autorun=not args.no_gui)
    main_loop(new_window=False if args.no_gui else None, quit=args.quit)