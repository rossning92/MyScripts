import sys
import os
import re
import time

SCRIPT_ROOT = os.path.realpath(os.path.dirname(__file__))
sys.path.append(os.path.join(SCRIPT_ROOT, "libs"))
sys.path.append(os.path.join(SCRIPT_ROOT, "bin"))

import run_python
from _script import *
from _term import *


GLOBAL_HOTKEY = os.path.join(tempfile.gettempdir(), "GlobalHotkey.ahk")


def execute_script(script, close_on_exit=None):
    args = update_env_var_explorer()
    script.execute(args=args, close_on_exit=close_on_exit)


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


def sort_scripts(scripts):
    while True:
        try:
            script_access_time, _ = get_all_script_access_time()

            def key(script):
                if script.script_path in script_access_time:
                    return max(
                        script_access_time[script.script_path],
                        os.path.getmtime(script.script_path),
                    )
                else:
                    return os.path.getmtime(script.script_path)

            return sorted(scripts, key=key, reverse=True)

        except FileNotFoundError:
            pass


def on_hotkey():
    pass


def register_hotkeys(scripts):
    hotkeys = {}
    for script in scripts:
        hotkey = script.meta["hotkey"]
        if hotkey is not None:
            print("Hotkey: %s: %s" % (hotkey, script.name))

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


def save_variables(variables):
    with open(get_variable_file(), "r") as f:
        data = json.load(f)

    data.update(variables)

    with open(get_variable_file(), "w") as f:
        json.dump(data, f, indent=4)


class VariableEditWindow(SearchWindow):
    def __init__(self, stdscr, vars, var_name):
        self.vars = vars
        self.var_name = var_name

        super().__init__(
            stdscr,
            self.vars[var_name] if var_name in self.vars else [],
            label=var_name + " :",
            text=(
                self.vars[var_name][-1]
                if var_name in self.vars and len(self.vars[var_name]) > 0
                else ""
            ),
        )

    def save_variable_val(self, val):
        if self.var_name not in self.vars:
            self.vars[self.var_name] = []
        try:
            self.vars[self.var_name].remove(val)
        except ValueError:
            pass
        self.vars[self.var_name].append(val)

        save_variables(self.vars)

    def on_enter_pressed(self):
        self.save_variable_val(self.get_text())
        self.close()

    def on_getch(self, ch):
        if ch == ord("\t"):
            val = self.get_selected_item()
            if val is not None:
                self.save_variable_val(val)
            self.close()
            return True

        return False


def get_variable_str_list(vars, var_names):
    result = []
    max_width = max([len(val_name) for val_name in var_names]) + 1
    for var_name in var_names:
        var_val = (
            vars[var_name][-1] if (var_name in vars and len(vars[var_name]) > 0) else ""
        )
        result.append(var_name.ljust(max_width) + ": " + var_val)
    return result


class VariableSearchWindow(SearchWindow):
    def __init__(self, stdscr, script):
        self.vars = get_all_variables()
        self.var_names = sorted(script.get_variable_names())
        self.items = []

        if len(self.var_names) > 0:
            self.update_items()
            super().__init__(stdscr, self.items, label="%s >" % (script.name))

    def update_items(self):
        self.items[:] = get_variable_str_list(self.vars, self.var_names)

    def on_enter_pressed(self):
        self.edit_variable()

    def on_getch(self, ch):
        if ch == ord("\t"):
            self.edit_variable()
            return True
        return False

    def edit_variable(self):
        index = self.get_selected_index()
        var_name = self.var_names[index]
        VariableEditWindow(self.stdscr, self.vars, var_name)
        self.update_items()
        self.input_.clear()


class State:
    def __init__(self):
        self.scripts = []
        self.modified_time = {}
        self.last_ts = 0
        self.hotkeys = {}
        self.execute_script = None


def add_keyboard_hooks(keyboard_hooks):
    if sys.platform != "linux":
        import keyboard

        keyboard.unhook_all()
        for hotkey, func in keyboard_hooks.items():
            keyboard.add_hotkey(hotkey, func)


def register_global_hotkeys(scripts):
    if platform.system() == "Windows":
        htk_definitions = ""
        with open(GLOBAL_HOTKEY, "w") as f:
            for item in scripts:
                hotkey = item.meta["globalHotkey"]
                if hotkey is not None:
                    print("Global Hotkey: %s: %s" % (hotkey, item.name))
                    hotkey = hotkey.replace("Ctrl+", "^")
                    hotkey = hotkey.replace("Alt+", "!")
                    hotkey = hotkey.replace("Shift+", "+")
                    hotkey = hotkey.replace("Win+", "#")

                    htk_definitions += (
                        f'{hotkey}::RunScript("{item.name}", "{item.script_path}")\n'
                    )

            # TODO: use templates
            f.write(
                """#SingleInstance, Force
#include libs/ahk/ExplorerHelper.ahk
; SetTitleMatchMode, 2
RunScript(name, path)
{
if WinExist(name)
{
    WinActivate % name
}
else if WinExist("Administrator:  " name)
{
    WinActivate % "Administrator:  " name
}
else
{
    WriteDefaultExplorerInfo()
    Run cmd /c """
                + sys.executable
                + ' "'
                + os.path.realpath("bin/run_script.py")
                + """" --new_window=None --console_title "%name%" --restart_instance 0 "%path%" || pause
}
}

#If not WinActive("ahk_exe vncviewer.exe")
"""
                + htk_definitions
                + """
#If
"""
            )

        subprocess.Popen([get_ahk_exe(), GLOBAL_HOTKEY], close_fds=True, shell=True)

    else:
        keyboard_hooks = {}
        for script in scripts:
            hotkey = script.meta["globalHotkey"]
            if hotkey is not None:
                print("Global Hotkey: %s: %s" % (hotkey, script.name))
                keyboard_hooks[hotkey] = lambda script=script: execute_script(script)
        add_keyboard_hooks(keyboard_hooks)


class MainWindow(SearchWindow):
    def __init__(self, stdscr):
        super().__init__(stdscr, items=state.scripts)

    def on_main_loop(self):
        # Reload scripts
        now = time.time()
        if now - state.last_ts > 2.0:
            if load_scripts(state.scripts, state.modified_time, autorun=True):
                state.hotkeys = register_hotkeys(state.scripts)
                register_global_hotkeys(state.scripts)
            state.scripts[:] = sort_scripts(state.scripts)

            state.last_ts = now

    def run_selected_script(self, close_on_exit=None):
        index = self.get_selected_index()
        if index >= 0:
            script = self.items[index]

            update_script_acesss_time(script)

            state.execute_script = lambda: execute_script(
                script, close_on_exit=close_on_exit
            )
            self.close()

    def on_getch(self, ch):
        if ch == ch == curses.ascii.ESC:
            return True

        elif ch == ord("\n"):
            self.run_selected_script()
            return True

        elif ch == ord("!"):
            self.run_selected_script(close_on_exit=False)
            return True

        elif ch == ord("\t"):
            script = self.get_selected_item()
            if script is not None:
                VariableSearchWindow(self.stdscr, script)
                return True

        elif ch in state.hotkeys:
            script = self.get_selected_item()
            if script is not None:
                script_abs_path = os.path.abspath(script.script_path)
                os.environ["_SCRIPT_PATH"] = script_abs_path

                state.execute_script = lambda: execute_script(state.hotkeys[ch])
                self.close()
                return True

        return False

    def on_update_screen(self):
        height = self.height

        try:
            script = self.get_selected_item()
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
                        self.stdscr.addstr(height + i, 0, s)

        except FileNotFoundError:  # Scripts have been removed
            pass

        self.height = height
        super().on_update_screen()


def main(stdscr):
    init_curses()
    MainWindow(stdscr)


def init():
    os.environ["PATH"] = os.pathsep.join(
        [os.path.join(SCRIPT_ROOT, "bin"), os.environ["PATH"]]
    )
    os.environ["PYTHONPATH"] = os.path.join(SCRIPT_ROOT, "libs")

    refresh_env()

    setup_nodejs(install=False)

    if is_instance_running():
        print("An instance is running. Exited.")
        sys.exit(0)


if __name__ == "__main__":
    # setup_console_font()

    init()

    state = State()

    while True:
        curses.wrapper(main)
        if state.execute_script is not None:
            state.execute_script()
            state.execute_script = None

            # HACK: workaround: key bindings will not work on windows.
            time.sleep(1)
        else:
            break
