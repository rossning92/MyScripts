# ruff: noqa: E402

import argparse
import logging
import logging.config
import os
import platform
import re
import shutil
import sys
import threading
import time
import traceback
from typing import Any, Dict, List, Optional, Tuple

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
    get_data_dir,
    get_default_script_config,
    get_script_config_file_path,
    get_script_variables,
    get_variable_edit_history_file,
    is_instance_running,
    setup_env_var,
    try_reload_scripts_autorun,
    update_variables,
)
from _scriptmanager import ScriptManager, execute_script
from _scriptserver import ScriptServer
from _shutil import (
    append_to_path_global,
    load_json,
    pause,
    quote_arg,
    refresh_env_vars,
    run_at_startup,
    save_json,
    setup_logger,
    setup_nodejs,
)
from utils.clip import set_clip
from utils.fileutils import read_last_line
from utils.menu import Menu
from utils.menu.confirm import confirm
from utils.menu.dictedit import DictEditMenu
from utils.menu.filemgr import FileManager
from utils.menu.logviewer import LogViewerMenu
from utils.menu.textinput import TextInput
from utils.timeutil import time_diff_str

REFRESH_INTERVAL_SECS = 60
KEY_CODE_CTRL_ENTER_WIN = 529


script_server: Optional[ScriptServer] = None


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


def format_variables(variables, variable_names, variable_prefix) -> List[str]:
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
        var_val = variables[name] if name in variables else ""
        result.append("env : " + short_var_names[i].ljust(max_width) + ": " + var_val)
    return result


class VariableEditMenu(DictEditMenu):
    def __init__(self, script: Script):
        self.variables = get_script_variables(script)
        self.variable_edit_history = load_json(get_variable_edit_history_file(), {})
        super().__init__(
            self.variables,
            prompt=f"{script.name}: vars:",
            on_dict_update=self.on_dict_update,
            on_dict_history_update=self.on_dict_history_update,
            dict_history=self.variable_edit_history,
        )

        self.add_command(self.__select_directory, hotkey="alt+d")

    def on_dict_history_update(self, history: Dict[str, List[Any]]):
        save_json(get_variable_edit_history_file(), history)

    def __select_directory(self):
        key = self.get_selected_key()
        if key is not None:
            dir_path = FileManager(goto=self.get_value(key)).select_directory()
            if dir_path is not None:
                self.set_dict_value(key, dir_path)

    def on_dict_update(self, d: Dict):
        update_variables(d)


def restart_program():
    if script_server is not None:
        script_server.stop_server()

    for t in threading.enumerate():
        if t is not threading.main_thread():
            logging.debug(f"Waiting {t} to exit...")
            t.join()

    os.execl(
        sys.executable,
        sys.executable,
        *(x for x in sys.argv if x != "--startup"),
    )


class _ScheduledScript:
    def __init__(self, script: Script, scheduled_time: float) -> None:
        self.script = script
        self.scheduled_time = scheduled_time

    def __str__(self) -> str:
        script_log_file = self.script.get_script_log_file()
        if os.path.exists(script_log_file):
            last_line = read_last_line(script_log_file)
        else:
            last_line = None

        return f"{time_diff_str(self.scheduled_time):<10} : {os.path.basename(self.script.script_path):<24} : {last_line}"


class _ScheduledScriptMenu(Menu[_ScheduledScript]):
    def __init__(self, script_manager: ScriptManager):
        items = [
            _ScheduledScript(script=script, scheduled_time=scheduled_time)
            for script, scheduled_time in script_manager.get_scheduled_scripts_run_time().items()
        ]
        super().__init__(items=items, prompt=": scheduled scripts:")

    def on_idle(self):
        self.update_screen()
        return super().on_idle()

    def on_enter_pressed(self):
        item = self.get_selected_item()
        if item is not None:
            script_log_file = item.script.get_script_log_file()
            if os.path.exists(script_log_file):
                LogViewerMenu(file=script_log_file).exec()


class _MyScriptMenu(Menu[Script]):
    def __init__(
        self, script_manager: ScriptManager, no_gui=False, run_script_and_quit=False
    ):
        self.script_manager = script_manager
        self.no_gui = no_gui
        self.last_refresh_time = 0.0
        self.is_refreshing = False
        self.__run_script_and_quit = run_script_and_quit
        self.__cmdline_args: Optional[str] = None
        self.__last_copy_time = 0.0

        super().__init__(
            items=self.script_manager.scripts,
            ascii_only=False,
            cancellable=run_script_and_quit,
            prompt=platform.node() + "$",
        )

        self.add_command(self._copy_cmdline, hotkey="ctrl+y")
        self.add_command(self._copy_script_path, hotkey="alt+y")
        self.add_command(self._delete_file)
        self.add_command(self._duplicate_script, hotkey="ctrl+d")
        self.add_command(self._edit_script_settings, hotkey="ctrl+s")
        self.add_command(self._edit_script, hotkey="ctrl+e")
        self.add_command(self._new_script, hotkey="ctrl+n")
        self.add_command(self._next_scheduled_script, hotkey="alt+t")
        self.add_command(self._run_without_close_on_exist, hotkey="alt+enter")
        self.add_command(self._run_without_close_on_exist, hotkey="ctrl+enter")
        self.add_command(self._reload_scripts, hotkey="ctrl+r")
        self.add_command(self._reload, hotkey="alt+l")
        self.add_command(self._rename_script_and_replace_all)
        self.add_command(self._rename_script)
        self.add_command(self._set_cmdline_args)

    def _reload(self):
        self.call_func_without_curses(lambda: restart_program())

    def _next_scheduled_script(self):
        _ScheduledScriptMenu(script_manager=self.script_manager).exec()

    def _set_cmdline_args(self):
        script = self.get_selected_script()
        if script:
            input = TextInput(prompt="args>").request_input()
            if input is not None:
                self.__cmdline_args = input

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

        for script in self.script_manager.get_scheduled_scripts_to_run():

            def exec_script():
                script.execute(
                    args=[],
                    close_on_exit=True,
                    restart_instance=False,
                    new_window=False,
                    background=True,
                )

            try:
                self.call_func_without_curses(exec_script)
            except Exception as ex:
                logging.error(f"Error on running scheduled script: {ex}")

    def match_item(self, keyword: str, script: Script) -> bool:
        if script.match_pattern(keyword):
            return True
        else:
            return super().match_item(keyword, script)

    def run_selected_script(self, close_on_exit=None):
        index = self.get_selected_index()
        if index >= 0:
            script = self.items[index]

            script.update_script_access_time()
            self.script_manager.sort_scripts()
            self.refresh()

            self.call_func_without_curses(
                lambda: execute_script(
                    script,
                    args=None if self.__cmdline_args is None else [self.__cmdline_args],
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

    def _on_register_hotkeys(self, hotkeys: Dict[str, Script]):
        for hotkey, script in hotkeys.items():
            self.add_command(
                lambda script=script: self._run_hotkey(script),
                hotkey=hotkey,
                name=script.name,
            )

    def _reload_scripts(self):
        if self.is_refreshing:
            return

        self.is_refreshing = True
        self.set_message("refreshing scripts...")

        def on_process():
            nonlocal self
            self.process_events()
            self.set_message(
                "refreshing scripts: %d" % len(self.script_manager.scripts)
            )

        self.script_manager.refresh_all_scripts(
            on_progress=on_process, on_register_hotkeys=self._on_register_hotkeys
        )
        self.set_message()
        self.update_last_refresh_time()
        self.is_refreshing = False
        return True

    def _edit_script_settings(self):
        script = self.get_selected_script()
        if script:
            edit_script_config(script.script_path)
            script.refresh_script()

    def _copy_cmdline(self):
        script = self.get_selected_script()
        if script:
            now = time.time()
            include_derivative = now < self.__last_copy_time + 1
            content = copy_script_path_to_clipboard(
                script,
                format="include" if include_derivative else "cmdline",
                with_variables=include_derivative,
            )
            self.set_message(
                f"copied to clipboard: {content}" if content else "copied to clipboard."
            )

            self.__last_copy_time = now

    def _copy_script_path(self):
        script = self.get_selected_script()
        if script:
            script_path = script.get_script_path()
            set_clip(script_path)
            self.set_message(f"copied: {script_path}")

    def _new_script_or_duplicate_script(self, duplicate=False):
        ref_script_path = self.get_selected_script_path()
        if ref_script_path:
            script_path = create_new_script(
                ref_script_path=ref_script_path, duplicate=duplicate
            )
            if script_path:
                script = Script(script_path)
                self.script_manager.scripts.insert(0, script)
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

    def _rename_script_and_replace_all(self):
        self._rename_script(
            replace_all_occurrence=True,
        )

    def _edit_script(self):
        script_path = self.get_selected_script_path()
        if script_path:
            self.call_func_without_curses(lambda: edit_myscript_script(script_path))

    def update_last_refresh_time(self):
        self.last_refresh_time = time.time()

    def _run_without_close_on_exist(self):
        try:
            self.run_selected_script(close_on_exit=False)
            self.clear_input(reset_selection=True)
        finally:
            # Reset last refresh time when key press event is processed
            self.update_last_refresh_time()

    def on_char(self, ch):
        self.set_message(None)

        try:
            if ch == "\t":
                script = self.get_selected_item()
                if script is not None:
                    w = VariableEditMenu(script)
                    if len(w.variables) > 0:
                        w.exec()
                return True
            else:
                return super().on_char(ch)
        finally:
            # Reset last refresh time when key press event is processed
            self.update_last_refresh_time()

    def on_enter_pressed(self):
        self.run_selected_script()
        self.clear_input(reset_selection=True)
        return True

    def on_escape_pressed(self):
        self.clear_input()

    def on_idle(self):
        try_reload_scripts_autorun(self.script_manager.scripts_autorun)

    def on_item_selection_changed(self, script: Optional[Script]):
        text = self.get_input()
        if script is not None and text and script.match_pattern(text):
            self.__cmdline_args = text
        else:
            self.__cmdline_args = None

    def on_update_screen(self, item_y_max: int):
        height = self._height

        if not self.is_refreshing:
            script = self.get_selected_item()
            if script is not None:
                preview: List[Tuple[str, str]] = []
                default_script_config = get_default_script_config()

                # Command line args
                if self.__cmdline_args is not None:
                    preview.append(("yellow", f"arg : {self.__cmdline_args}"))

                # Preview variables
                try:
                    vars = get_script_variables(script)
                    if len(vars) > 0:
                        preview.extend(
                            [
                                ("yellow", x)
                                for x in format_variables(
                                    vars,
                                    sorted(script.get_variable_names()),
                                    script.get_public_variable_prefix(),
                                )
                            ]
                        )
                except FileNotFoundError:  # Scripts have been removed
                    logging.warning(
                        "Error on reading variables from script, script does not exist: %s"
                        % script.script_path
                    )

                # Preview script configs
                config_preview = {}
                for name, value in script.cfg.items():
                    if value != default_script_config[name]:
                        config_preview[f"cfg : {name}"] = str(value)
                preview.extend(
                    [("yellow", x) for x in format_key_value_pairs(config_preview)]
                )

                height = max(5, height - len(preview) - 1)
                for i, (color, s) in enumerate(preview):
                    if height + i >= self._height:
                        break
                    self.draw_text(height + i, 0, s, color=color)

        super().on_update_screen(item_y_max=height)

    def _run_hotkey(self, script: Script):
        selected_script = self.get_selected_item()
        if selected_script is not None:
            os.environ["SCRIPT"] = os.path.abspath(selected_script.script_path)

            self.call_func_without_curses(
                lambda script=script: execute_script(script, no_gui=self.no_gui)
            )
            if script.cfg["reloadScriptsAfterRun"]:
                logging.info("Reload scripts after running: %s" % script.name)
                self._reload_scripts()
            else:
                if script.cfg["updateSelectedScriptAccessTime"]:
                    selected_script.update_script_access_time()
                self.script_manager.sort_scripts()
                self.refresh()
            return True


def _main(no_gui=False):
    global script_server

    start_daemon = not is_instance_running()
    logging.debug(f"start_daemon: {start_daemon}")

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

    if start_daemon:
        script_server = ScriptServer()
        script_server.start_server()

    script_manager = ScriptManager(start_daemon=start_daemon, startup=args.startup)

    run_script_and_quit = args.cmd == "r" or args.cmd == "run"
    while True:  # repeat if _MyScriptMenu throws exceptions
        try:
            _MyScriptMenu(
                script_manager=script_manager,
                no_gui=no_gui,
                run_script_and_quit=run_script_and_quit,
            ).exec()
            if run_script_and_quit:
                break

        except Exception:
            traceback.print_exc(file=sys.stdout)
            pause()


if __name__ == "__main__":
    log_file = os.path.join(get_data_dir(), "MyScripts.log")
    setup_logger(log_to_stderr=False, log_file=log_file)

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
    parser.add_argument(
        "-t",
        "--tmux",
        action="store_true",
        help="Run in tmux.",
    )
    args = parser.parse_args()

    if args.tmux:
        tmux_exec = shutil.which("tmux")
        if tmux_exec is None:
            raise Exception("tmux is not installed.")
        os.execl(
            tmux_exec,
            "tmux",
            "-f",
            os.path.join(MYSCRIPT_ROOT, "settings", "tmux", ".tmux.conf"),
            "new",
            sys.executable,
            *(x for x in sys.argv if x not in ("-t", "--tmux")),
        )

    run_at_startup(
        name="MyScripts",
        cmdline=quote_arg(os.path.join(MYSCRIPT_ROOT, "myscripts.cmd")) + " --startup",
    )

    _main(no_gui=args.no_gui)
