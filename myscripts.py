import argparse
import ctypes
import curses
import logging
import logging.config
import os
import platform
import re
import sys
import time
import traceback
from typing import Optional

MYSCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(MYSCRIPT_ROOT, "libs"))
sys.path.append(os.path.join(MYSCRIPT_ROOT, "bin"))


from _ext import (
    copy_script_path_to_clipboard,
    create_new_script,
    edit_myscript_script,
    edit_script_config,
    rename_script,
)
from _script import (
    Script,
    get_all_variables,
    get_default_script_config,
    get_script_config_file_path,
    get_script_variables,
    get_temp_dir,
    is_instance_running,
    save_variables,
    set_variable_value,
    setup_env_var,
    try_reload_scripts_autorun,
    update_script_access_time,
)
from _scriptmanager import ScriptManager, execute_script
from _scriptserver import ScriptServer
from _shutil import (
    append_to_path_global,
    pause,
    quote_arg,
    refresh_env_vars,
    run_at_startup,
    set_clip,
    setup_logger,
    setup_nodejs,
)
from utils.menu import Menu
from utils.menu.confirm import confirm
from utils.menu.filemgr import FileManager

REFRESH_INTERVAL_SECS = 60
KEY_CODE_CTRL_ENTER_WIN = 529


def setup_console_font():
    if sys.platform == "win32":
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


class VariableEditMenu(Menu):
    def __init__(self, vars, var_name):
        self.vars = vars
        self.var_name = var_name
        self.enter_pressed = False

        super().__init__(
            items=self.vars[var_name] if var_name in self.vars else [],
            prompt=var_name + "=",
            text="",
        )

    def save_variable_val(self, val):
        set_variable_value(self.vars, self.var_name, val)

    def on_enter_pressed(self):
        self.save_variable_val(self.get_text())
        self.enter_pressed = True
        self.close()

    def on_char(self, ch):
        if ch == "\t":
            val = self.get_selected_item()
            if val is not None:
                self.set_input(val)
            return True
        elif ch == curses.KEY_DC:  # delete key
            i = self.get_selected_index()
            del self.vars[self.var_name][i]
            save_variables(self.vars)
            return True
        else:
            return super().on_char(ch)


def format_key_value_pairs(kvp):
    result = []
    key_length = [len(key) for key in kvp]
    if key_length:
        max_key_length = max(key_length) + 1
    else:
        max_key_length = 0
    for key, value in kvp.items():
        result.append(key.ljust(max_key_length) + ": " + value)
    return result


def format_variables(variables, variable_names, variable_prefix):
    result = []
    short_var_names = [
        re.sub("^" + re.escape(variable_prefix), "", x) for x in variable_names
    ]
    var_name_length = [len(x) for x in short_var_names]
    if var_name_length:
        max_width = max(var_name_length) + 1
    else:
        max_width = 0
    for i, name in enumerate(variable_names):
        var_val = (
            variables[name][0]
            if (name in variables and len(variables[name]) > 0)
            else ""
        )
        result.append(short_var_names[i].ljust(max_width) + ": " + var_val)
    return result


class VariableMenu(Menu):
    def __init__(self, script: Script):
        super().__init__(prompt=f"{script.name}> vars")
        self.variables = get_all_variables()
        self.variable_names = sorted(script.get_variable_names())
        self.variable_prefix = script.get_public_variable_prefix()
        self.enter_pressed = False

        self.add_hotkey("ctrl+d", self._select_directory)

        if len(self.variable_names) > 0:
            self.update_items()

        self.set_message("Shortcuts: [^d] select dir")

    def _select_directory(self):
        index = self.get_selected_index()
        if index >= 0:
            variable_name = self.variable_names[index]

            dir_path = FileManager().select_directory()
            if dir_path is not None:
                set_variable_value(self.variables, variable_name, dir_path)
                self.update_items()

    def update_items(self):
        self.items[:] = format_variables(
            self.variables, self.variable_names, self.variable_prefix
        )

    def on_enter_pressed(self):
        self.enter_pressed = True
        self.close()

    def on_char(self, ch):
        if ch == "\t":
            self.edit_variable()
            return True
        elif ch == "C":
            index = self.get_selected_index()
            name = self.variable_names[index]
            if name in self.variables and len(self.variables[name]) > 0:
                val = self.variables[name][0]
                set_clip(val)
                self.close()
            return True
        else:
            return super().on_char(ch)

    def edit_variable(self):
        index = self.get_selected_index()
        var_name = self.variable_names[index]
        w = VariableEditMenu(self.variables, var_name)
        w.exec()
        # if w.enter_pressed:
        #     self.close()
        self.update_items()
        self.clear_input()


def restart_program():
    os.execl(
        sys.executable,
        sys.executable,
        *(x for x in sys.argv if x != "--startup"),
    )


class MainWindow(Menu[Script]):
    def __init__(self, no_gui=False, run_script_and_quit=False):
        self.no_gui = no_gui
        self.last_refresh_time = 0.0
        self.is_refreshing = False
        self.__run_script_and_quit = run_script_and_quit

        super().__init__(
            items=script_manager.scripts,
            ascii_only=False,
            cancellable=run_script_and_quit,
            prompt=platform.node() + "$",
        )

        self.add_hotkey("ctrl+r", self._reload_scripts)
        self.add_hotkey("shift+m", self._edit_script_config)
        self.add_hotkey("shift+c", self._copy_to_clipboard)
        self.add_hotkey("shift+i", self._copy_to_clipboard_include_derivative)
        self.add_hotkey("ctrl+n", self._new_script)
        self.add_hotkey("ctrl+d", self._duplicate_script)
        self.add_hotkey("shift+n", self._rename_script)
        self.add_hotkey(
            "shift+b", lambda: self._rename_script(replace_all_occurrence=True)
        )
        self.add_hotkey("ctrl+e", self._edit_script)
        self.add_hotkey("ctrl+k", self._delete_file)
        self.add_hotkey("?", self._help)

    def _delete_file(self):
        script_path = self.get_selected_script_path()
        if script_path and confirm(f'Delete "{script_path}"?'):
            os.remove(script_path)

            script_config_path = get_script_config_file_path(script_path)
            if os.path.exists(script_config_path):
                os.remove(script_config_path)

            self._reload_scripts()

    def on_main_loop(self):
        # Reload scripts
        now = time.time()
        if (
            now - self.last_key_pressed_timestamp > REFRESH_INTERVAL_SECS
            and now - self.last_refresh_time > REFRESH_INTERVAL_SECS
        ):
            self._reload_scripts()

        script_manager.check_scheduled_scripts()

    def run_selected_script(self, close_on_exit=None):
        index = self.get_selected_index()
        if index >= 0:
            script = self.items[index]

            update_script_access_time(script)
            script_manager.sort_scripts()
            self.refresh()

            self.call_func_without_curses(
                lambda: execute_script(
                    script,
                    close_on_exit=close_on_exit,
                    no_gui=self.no_gui,
                )
            )

            if self.__run_script_and_quit:
                self.close()
                return

            if script.cfg["reloadScriptsAfterRun"]:
                logging.info("Reload scripts after running: %s" % script.name)
                self._reload_scripts()

    def get_selected_script(self) -> Optional[Script]:
        index = self.get_selected_index()
        if index >= 0:
            return self.items[index]
        else:
            return None

    def get_selected_script_path(self) -> Optional[str]:
        script = self.get_selected_item()
        if script is not None:
            return script.script_path
        else:
            return None

    def _reload_scripts(self):
        if self.is_refreshing:
            return

        self.is_refreshing = True
        self.set_message("refreshing scripts...")

        def on_process():
            nonlocal self
            self.process_events()
            self.set_message("refreshing scripts: %d" % len(script_manager.scripts))

        script_manager.refresh_all_scripts(on_progress=on_process)
        self.set_message()
        self.update_last_refresh_time()
        self.is_refreshing = False
        return True

    def _edit_script_config(self):
        script_path = self.get_selected_script_path()
        if script_path:
            edit_script_config(script_path)
            # reload the current script
            index = self.get_selected_index()
            self.items[index] = Script(script_path)
            self.clear_input()

    def _copy_to_clipboard(self):
        script = self.get_selected_script()
        if script:
            content = copy_script_path_to_clipboard(script)
            self.set_message(
                f"Content copied: {content}" if content else "Copied to clipboard."
            )

    def _copy_to_clipboard_include_derivative(self):
        script = self.get_selected_script()
        if script:
            content = copy_script_path_to_clipboard(
                script, format="include", with_variables=True
            )
            self.set_message(f"copied to clipboard: {content}")

    def _new_script_or_duplicate_script(self, duplicate=False):
        ref_script_path = self.get_selected_script_path()
        if ref_script_path:
            script_path = create_new_script(
                ref_script_path=ref_script_path, duplicate=duplicate
            )
            if script_path:
                script = Script(script_path)
                script_manager.scripts.insert(0, script)
        self.clear_input()

    def _new_script(self):
        self._new_script_or_duplicate_script(duplicate=False)

    def _duplicate_script(self):
        self._new_script_or_duplicate_script(duplicate=True)

    def _rename_script(self, replace_all_occurrence=False):
        def on_progress(msg: str):
            nonlocal self
            self.process_events()
            self.set_message(msg)

        script_path = self.get_selected_script_path()
        if script_path:
            self.set_message("searching scripts to rename...")
            if rename_script(
                script_path,
                on_progress=on_progress,
                replace_all_occurrence=replace_all_occurrence,
            ):
                self._reload_scripts()
            self.set_message()
        self.clear_input()

    def _edit_script(self):
        script_path = self.get_selected_script_path()
        if script_path:
            self.call_func_without_curses(lambda: edit_myscript_script(script_path))

    def _help(self):
        items = []
        items.extend(self._hotkeys.values())
        items.extend(script_manager.hotkeys.values())
        w = Menu(prompt="all hotkeys", items=items)
        w.exec()

    def update_last_refresh_time(self):
        self.last_refresh_time = time.time()

    def on_char(self, ch):
        self.set_message(None)

        try:
            if ch == KEY_CODE_CTRL_ENTER_WIN or (
                # Alt + Enter is pressed
                # (note that "\x1b" is the ASCII “Escape” control character)
                self.prev_key == "\x1b"
                and ch == "\n"
            ):
                self.run_selected_script(close_on_exit=False)
                self.clear_input()
                return True

            elif ch == "\n":
                self.run_selected_script()
                self.clear_input()
                return True

            elif ch == "\t":
                script = self.get_selected_item()
                if script is not None:
                    w = VariableMenu(script)
                    if w.variable_names:
                        w.exec()
                        if w.enter_pressed:
                            self.run_selected_script()
                return True

            elif ch == "L":
                self.call_func_without_curses(lambda: restart_program())

            elif ch in script_manager.hotkeys:
                script = script_manager.hotkeys[ch]
                selected_script = self.get_selected_item()
                if selected_script is not None:
                    os.environ["SCRIPT"] = os.path.abspath(selected_script.script_path)

                    self.call_func_without_curses(
                        lambda: execute_script(script, no_gui=self.no_gui)
                    )
                    if script.cfg["reloadScriptsAfterRun"]:
                        logging.info("Reload scripts after running: %s" % script.name)
                        self._reload_scripts()
                    else:
                        if script.cfg["updateSelectedScriptAccessTime"]:
                            update_script_access_time(selected_script)
                        script_manager.sort_scripts()
                        self.refresh()
                    return True

            elif ch == "\x1b":
                return True

            else:
                return super().on_char(ch)

        finally:
            # Reset last refresh time when key press event is processed
            self.update_last_refresh_time()

    def on_idle(self):
        try_reload_scripts_autorun(script_manager.scripts_autorun)

    def on_update_screen(self, height: int):
        height = self._height

        if not self.is_refreshing:
            script = self.get_selected_item()
            if script is not None:
                preview = []
                default_script_config = get_default_script_config()

                # Preview script configs
                config_preview = {}
                for name, value in script.cfg.items():
                    if value != default_script_config[name]:
                        config_preview[f"[Cfg] {name}"] = str(value)
                preview += format_key_value_pairs(config_preview)

                # Preview variables
                try:
                    vars = get_script_variables(script)
                    if len(vars) > 0:
                        preview += format_variables(
                            vars,
                            sorted(script.get_variable_names()),
                            script.get_public_variable_prefix(),
                        )
                except FileNotFoundError:  # Scripts have been removed
                    logging.warning(
                        "Error on reading variables from script, script does not exist: %s"
                        % script.script_path
                    )

                height = max(5, height - len(preview))
                for i, s in enumerate(preview):
                    if height + i >= self._height:
                        break
                    self.draw_text(height + i, 0, s)

        super().on_update_screen(height=height)


def _init(no_gui=False):
    if not no_gui and is_instance_running():
        print("An instance is already running, exiting.")
        sys.exit(0)

    logging.info("Python executable: %s" % sys.executable)

    # Add bin folder to PATH
    bin_dir = os.path.join(MYSCRIPT_ROOT, "bin")
    append_to_path_global(bin_dir)

    # Add Python's "Scripts" dir to PATH
    script_dir = os.path.abspath(os.path.join(sys.prefix, "Scripts"))
    append_to_path_global(script_dir)

    setup_env_var(os.environ)

    refresh_env_vars()

    setup_nodejs(install=False)

    if not no_gui:
        script_server = ScriptServer()
        script_server.start_server()


def _main_loop(no_gui=False, run_script_and_quit=False):
    _init(no_gui=no_gui)
    while True:  # repeat if MainWindow throws exceptions
        try:
            MainWindow(no_gui=no_gui, run_script_and_quit=run_script_and_quit).exec()
            if run_script_and_quit:
                break

        except Exception:
            traceback.print_exc(file=sys.stdout)
            pause()


if __name__ == "__main__":
    log_file = os.path.join(get_temp_dir(), "MyScripts.log")
    logging.basicConfig(
        filename=log_file,
        filemode="w",
        format="%(asctime)s %(levelname).1s %(filename)-10s: %(funcName)-10s: %(message)s",
        level=logging.DEBUG,
    )

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "cmd",
        nargs="?",
        help="The cmd can be `run` which executes a script and exit to the terminal.",
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
        cmdline=quote_arg(os.path.join(MYSCRIPT_ROOT, "myscripts.cmd")) + " --startup",
    )

    # setup_console_font()
    script_manager = ScriptManager(no_gui=args.no_gui, startup=args.startup)
    if args.cmd == "r" or args.cmd == "run":
        _main_loop(no_gui=True, run_script_and_quit=True)
    else:
        _main_loop(no_gui=args.no_gui)
