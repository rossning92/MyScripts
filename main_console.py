import argparse
import os
import sys
import time
import traceback

SCRIPT_ROOT = os.path.realpath(os.path.dirname(__file__))
sys.path.append(os.path.join(SCRIPT_ROOT, "libs"))
sys.path.append(os.path.join(SCRIPT_ROOT, "bin"))

import curses
import logging
import re
import subprocess

from _script import (
    get_all_script_access_time,
    get_all_variables,
    get_data_dir,
    get_script_variables,
    is_instance_running,
    reload_scripts,
    save_variables,
    update_script_access_time,
)
from _shutil import (
    add_to_path,
    get_ahk_exe,
    refresh_env_vars,
    setup_logger,
    setup_nodejs,
    start_process,
    update_env_var_explorer,
)
from _template import render_template_file
from _term import Menu, init_curses

REFRESH_INTERVAL_SECS = 60
GLOBAL_HOTKEY = os.path.join(get_data_dir(), "GlobalHotkey.ahk")
script_root = os.path.dirname(os.path.abspath(__file__))


def execute_script(script, close_on_exit=None):
    refresh_env_vars()
    args = update_env_var_explorer()
    script.execute(args=args, close_on_exit=close_on_exit, single_instance=False)


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


def register_hotkeys(scripts):
    hotkeys = {}
    for script in scripts:
        hotkey = script.cfg["hotkey"]
        if hotkey:
            logging.info("Hotkey: %s: %s" % (hotkey, script.name))

            hotkey = hotkey.lower()
            key = hotkey[-1].lower()

            if "ctrl+" in hotkey:
                ch = curses.ascii.ctrl(ord(key))
                hotkeys[ch] = script
            elif "shift+" in hotkey or "alt+" in hotkey:
                # HACK: use `shift+` in place of `alt+`
                ch = ord(key.upper())
                hotkeys[ch] = script

    return hotkeys


class VariableEditWindow(Menu):
    def __init__(self, stdscr, vars, var_name):
        self.vars = vars
        self.var_name = var_name

        super().__init__(
            items=self.vars[var_name] if var_name in self.vars else [],
            stdscr=stdscr,
            label=var_name + " :",
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
    max_width = max([len(val_name) for val_name in var_names]) + 1
    for var_name in var_names:
        var_val = (
            vars[var_name][0] if (var_name in vars and len(vars[var_name]) > 0) else ""
        )
        result.append(var_name.ljust(max_width) + ": " + var_val)
    return result


class VariableWindow(Menu):
    def __init__(self, stdscr, script):
        super().__init__(stdscr=stdscr, label="%s >" % (script.name))
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
        VariableEditWindow(self.stdscr, self.vars, var_name).exec()
        self.update_items()
        self.input_.clear()


class ScriptManager:
    def __init__(self):
        self.scripts = []
        self.modified_time = {}
        self.last_refresh_time = 0
        self.hotkeys = {}
        self.execute_script = None

    def update_access_time(self):
        access_time, _ = get_all_script_access_time()
        for script in self.scripts:
            if script.script_path in access_time:
                self.modified_time[script.script_path] = max(
                    self.modified_time[script.script_path],
                    access_time[script.script_path],
                )

    def sort_scripts(self):
        self.update_access_time()
        self.scripts[:] = sorted(
            self.scripts,
            key=lambda script: self.modified_time[script.script_path],
            reverse=True,
        )

    def refresh_all_scripts(self):
        if reload_scripts(self.scripts, self.modified_time, autorun=True):
            self.hotkeys = register_hotkeys(self.scripts)
            register_global_hotkeys(self.scripts)
        self.sort_scripts()
        self.last_refresh_time = time.time()


def add_keyboard_hooks(keyboard_hooks):
    if sys.platform != "linux":
        import keyboard

        keyboard.unhook_all()
        for hotkey, func in keyboard_hooks.items():
            keyboard.add_hotkey(hotkey, func)


def register_global_hotkeys_linux(scripts):
    s = (
        f"control+q\n"
        f"  gnome-terminal -- python3 {script_root}/main_console.py -q\n"
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
            s += f"  python3 {script_root}/bin/start_script.py {item.script_path}\n\n"

    with open(os.path.expanduser("~/.sxhkdrc"), "w") as f:
        f.write(s)
    subprocess.call(["pkill", "-USR1", "sxhkd"])
    # start_process(["sxhkd", "-c", os.path.expanduser("~/.sxhkdrc")])


def register_global_hotkeys_win(scripts):
    hotkey_def = ""
    hotkeys = ""
    hotkey_seq_def = ""

    for item in scripts:
        hotkey = item.cfg["globalHotkey"]
        alias = item.cfg["alias"]
        if hotkey or alias:
            func_name = re.sub("[^0-9a-zA-Z]+", "_", item.name)

            hotkey_def += (
                f"{func_name}() {{\n"
                "    Send {Alt Up}{Ctrl Up}{Shift Up}\n"  # prevent wrong windows getting focus
                f'    RunScript("{item.name}", "{item.script_path}")\n'
                "}\n"
            )

            if hotkey:
                logging.info("GlobalHotkey: %s: %s" % (hotkey, item.name))
                hotkey = hotkey.lower()
                hotkey = hotkey.replace("ctrl+", "^")
                hotkey = hotkey.replace("alt+", "!")
                hotkey = hotkey.replace("shift+", "+")
                hotkey = hotkey.replace("win+", "#")
                hotkeys += f"{hotkey}::{func_name}()\n"

            if alias:
                hotkey_seq_def += f'{alias}: "{func_name}", '

    hotkey_seq_def = hotkey_seq_def.rstrip(", ")

    cmdline = '%s "%s"' % (
        sys.executable,
        os.path.realpath("bin/start_script.py"),
    )

    render_template_file(
        "GlobalHotkey.ahk",
        GLOBAL_HOTKEY,
        context={
            "cmdline": cmdline,
            "hotkey_def": hotkey_def,
            "hotkeys": hotkeys,
            "hotkey_seq_def": hotkey_seq_def,
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


class MainWindow(Menu):
    def __init__(self, stdscr):
        super().__init__(
            items=script_manager.scripts,
            stdscr=stdscr,
            ascii_only=True,
            cancellable=False,
        )

    def on_main_loop(self):
        # Reload scripts
        now = time.time()
        if (
            now - self.last_key_pressed_timestamp > REFRESH_INTERVAL_SECS
            and now - script_manager.last_refresh_time > REFRESH_INTERVAL_SECS
        ):

            self.set_message("Reloading scripts...")
            script_manager.refresh_all_scripts()
            self.set_message(None)

    def run_selected_script(self, close_on_exit=None):
        index = self.get_selected_index()
        if index >= 0:
            script = self.items[index]

            update_script_access_time(script)
            script_manager.sort_scripts()

            script_manager.execute_script = lambda: execute_script(
                script, close_on_exit=close_on_exit
            )

            self.close()

    def on_char(self, ch):
        if ch == curses.ascii.ctrl(ord("r")):
            self.set_message("Reloading scripts...")
            script_manager.refresh_all_scripts()
            self.set_message(None)
            return True

        elif ch == ord("\n"):
            self.run_selected_script()
            return True

        elif ch == ord("!"):
            self.run_selected_script(close_on_exit=False)
            return True

        elif ch == ord("\t"):
            script = self.get_selected_text()
            if script is not None:
                w = VariableWindow(self.stdscr, script)
                if w.var_names:
                    w.exec()
                    if w.enter_pressed:
                        self.run_selected_script()
            return True

        elif ch == ord("L"):
            sys.exit(1)

        elif ch in script_manager.hotkeys:
            script = self.get_selected_text()
            if script is not None:
                script_abs_path = os.path.abspath(script.script_path)
                os.environ["SCRIPT"] = script_abs_path

                script_manager.execute_script = lambda: (
                    execute_script(script_manager.hotkeys[ch]),
                    # Other script may update the script access time
                    # Hence, we need to sort the script list
                    script_manager.sort_scripts(),
                )
                self.close()
                return True

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
                            self.stdscr.addstr(height + i, 0, s)
                        except:
                            pass

        except FileNotFoundError:  # Scripts have been removed
            pass

        self.height = height
        super().on_update_screen()


def curse_main(stdscr):
    init_curses(stdscr)
    MainWindow(stdscr).exec()


def init():
    setup_logger(log_file=os.path.join(get_data_dir(), "MyScripts.log"), stdout=False)

    # Add bin folder to PATH
    bin_dir = os.path.join(SCRIPT_ROOT, "bin")
    add_to_path(bin_dir)

    user_site = subprocess.check_output(
        [sys.executable, "-m", "site", "--user-site"], universal_newlines=True
    ).strip()
    script_dir = os.path.abspath(os.path.join(user_site, "..", "Scripts"))
    add_to_path(script_dir)

    os.environ["PATH"] = os.pathsep.join([bin_dir, os.environ["PATH"]])

    os.environ["PYTHONPATH"] = os.path.join(SCRIPT_ROOT, "libs")

    refresh_env_vars()

    setup_nodejs(install=False)

    if is_instance_running():
        logging.info("An instance is running. Exited.")
        sys.exit(0)


def main_loop(quit=False):
    while True:
        try:
            curses.wrapper(curse_main)
            if script_manager.execute_script is not None:
                script_manager.execute_script()
                script_manager.execute_script = None

                if quit:
                    break

                # HACK: workaround: key bindings will not work on windows.
                # time.sleep(1)
            else:
                break

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
    args = parser.parse_args()

    # setup_console_font()
    init()
    script_manager = ScriptManager()
    main_loop(quit=args.quit)
