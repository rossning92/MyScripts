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
    edit_script,
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
    setup_nodejs,
)
from utils.clip import set_clip
from utils.fileutils import read_last_line
from utils.logger import setup_logger
from utils.menu import Menu
from utils.menu.confirm import confirm
from utils.menu.dictedit import DictEditMenu
from utils.menu.filemgr import FileManager
from utils.menu.logviewer import LogViewerMenu
from utils.menu.textinput import TextInput
from utils.platform import is_termux
from utils.timeutil import time_diff_str
from utils.tmux import is_in_tmux

REFRESH_INTERVAL_SECS = 60
KEY_CODE_CTRL_ENTER_WIN = 529

# If the first character is a leader key in the search keyword, we will try to
# do an exact match for script alias only.
LEADER_KEY = " "


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
    for i, (full_name, short_name) in enumerate(zip(variable_names, short_var_names)):
        var_val = variables.get(full_name, "")
        result.append(
            ("env : " if i == 0 else " " * 6) + f"{short_name:<16} : {var_val}"
        )
    return result


class EditVariableMenu(DictEditMenu):
    def __init__(self, script: Script):
        self.variables = get_script_variables(script)
        self.variable_edit_history = load_json(get_variable_edit_history_file(), {})
        super().__init__(
            self.variables,
            prompt=f"{script.name} : vars",
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

        return f"{time_diff_str(self.scheduled_time):<4} : {os.path.basename(self.script.script_path)} : {last_line}"


class _ScheduledScriptMenu(Menu[_ScheduledScript]):
    def __init__(self, script_manager: ScriptManager):
        items = [
            _ScheduledScript(script=script, scheduled_time=scheduled_time)
            for script, scheduled_time in script_manager.get_scheduled_scripts_run_time().items()
        ]
        super().__init__(items=items, prompt="scheduled scripts")

    def on_idle(self):
        self.update_screen()
        return super().on_idle()

    def on_enter_pressed(self):
        item = self.get_selected_item()
        if item is not None:
            script_log_file = item.script.get_script_log_file()
            if os.path.exists(script_log_file):
                LogViewerMenu(files=[script_log_file]).exec()


def get_scheduled_script_log_preview(script_manager: ScriptManager) -> List[str]:
    logs: List[str] = []
    for (
        script,
        scheduled_time,
    ) in script_manager.get_scheduled_scripts_run_time().items():
        script_log_file = script.get_script_log_file()
        if os.path.exists(script_log_file):
            last_line = read_last_line(script_log_file)
            logs.append(
                f"{time_diff_str(scheduled_time):<4} : {os.path.basename(script.script_path)} : {last_line}"
            )
    return logs


class _MyScriptMenu(Menu[Script]):
    def __init__(
        self,
        script_manager: ScriptManager,
        no_daemon=False,
        run_script_and_quit=False,
        input_text: Optional[str] = None,
        cmdline_args: Optional[List[str]] = None,
        out_to_file: Optional[str] = None,
        prompt: Optional[str] = None,
    ):
        self.script_manager = script_manager
        self.__no_daemon = no_daemon
        self.last_refresh_time = 0.0
        self.is_refreshing = False
        self.__run_script_and_quit = run_script_and_quit
        self.__cmdline_args: List[str] = cmdline_args if cmdline_args else []
        self.__auto_infer_cmdline_args: bool = not bool(cmdline_args)
        self.__last_copy_time = 0.0
        self.__filemgr = FileManager()
        self.__out_to_file = out_to_file

        super().__init__(
            items=self.script_manager.scripts,
            ascii_only=False,
            cancellable=run_script_and_quit,
            prompt=prompt if prompt else platform.node(),
            text=input_text,
            wrap_text=True,
        )

        self.add_command(self._copy_cmdline, hotkey="ctrl+y")
        self.add_command(self._copy_to, hotkey="alt+y")
        self.add_command(self._copy_file_path)
        self.add_command(self._delete_file, hotkey="ctrl+k")
        self.add_command(self._duplicate_script, hotkey="ctrl+d")
        self.add_command(self._edit_script_settings, hotkey="ctrl+s")
        self.add_command(self._edit_script, hotkey="ctrl+e")
        self.add_command(self._edit_script_vim)
        self.add_command(self._new_script, hotkey="ctrl+n")
        self.add_command(self._next_scheduled_script, hotkey="alt+t")
        self.add_command(self._run_script_no_close, hotkey="alt+enter")
        self.add_command(self._run_script_no_close, hotkey="ctrl+enter")
        self.add_command(self._reload_scripts, hotkey="ctrl+r")
        self.add_command(self._reload, hotkey="alt+l")
        self.add_command(self._rename_script_and_replace_all)
        self.add_command(self._rename_script, hotkey="alt+n")
        self.add_command(self._set_cmdline_args)

    def _reload(self):
        self.call_func_without_curses(lambda: restart_program())

    def _next_scheduled_script(self):
        _ScheduledScriptMenu(script_manager=self.script_manager).exec()

    def _set_cmdline_args(self):
        script = self.get_selected_script()
        if script:
            input = TextInput(prompt="args").request_input()
            if input is not None:
                self.__cmdline_args[:] = [input]

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

    def match_item(self, keyword: str, script: Script, index: int) -> bool:
        if keyword[0:1] == LEADER_KEY:
            return script.alias == keyword[1:]
        else:
            if script.match_pattern(keyword):
                return True
            else:
                return super().match_item(patt=keyword, item=script, index=index)

    def _run_selected_script(self, close_on_exit=None):
        index = self.get_selected_index()
        if index >= 0:
            script = self.items[index]

            script.update_script_access_time()
            self.script_manager.sort_scripts()
            self.refresh()

            self.call_func_without_curses(
                lambda: execute_script(
                    script,
                    args=self.__cmdline_args if self.__cmdline_args else None,
                    cd=len(self.__cmdline_args) == 0,
                    close_on_exit=close_on_exit,
                    no_daemon=self.__no_daemon,
                    out_to_file=self.__out_to_file,
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
        self.delete_commands_if(lambda cmd: cmd.name.startswith("run: "))
        for hotkey, script in hotkeys.items():
            self.add_command(
                lambda script=script: self._run_hotkey(script),
                hotkey=hotkey,
                name="run: " + script.name,
            )

    def _reload_scripts(self):
        if self.is_refreshing:
            return

        self.is_refreshing = True
        self.set_message("refreshing scripts...")

        def on_progress():
            nonlocal self
            self.process_events()
            self.set_message(
                "refreshing scripts: %d" % len(self.script_manager.scripts)
            )

        self.script_manager.refresh_all_scripts(
            on_progress=on_progress, on_register_hotkeys=self._on_register_hotkeys
        )
        self.set_message()
        self.update_last_refresh_time()
        self.update_matched_items()
        self.is_refreshing = False

        if self.__run_script_and_quit:
            # If only one script is matched, run it directly.
            if len(self._matched_item_indices) == 1:
                self._run_selected_script()

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

    def _copy_to(self):
        script = self.get_selected_script()
        if script:
            script_path = script.get_script_path()
            self.__filemgr.copy_to(script_path)

    def _copy_file_path(self):
        script = self.get_selected_script()
        if script:
            script_path = script.get_script_path()
            set_clip(script_path)
            self.set_message(f"copied: {script_path}")

    def _new_script_or_duplicate_script(
        self, src_script_path: Optional[str], duplicate=False
    ):
        script_dirs = sorted(
            set(os.path.dirname(x.name) + "/" for x in self.script_manager.scripts)
        )
        script_path = create_new_script(
            src_script_path=src_script_path,
            script_dirs=script_dirs,
            duplicate=duplicate,
        )
        if script_path:
            script = Script(script_path)
            self.script_manager.scripts.insert(0, script)
        self.clear_input()

    def _new_script(self):
        src_script_path = self.get_selected_script_path()
        self._new_script_or_duplicate_script(src_script_path=src_script_path)

    def _duplicate_script(self):
        src_script_path = self.get_selected_script_path()
        if src_script_path:
            self._new_script_or_duplicate_script(
                src_script_path=src_script_path, duplicate=True
            )

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
            self.call_func_without_curses(lambda: edit_script(script_path))

    def _edit_script_vim(self):
        script_path = self.get_selected_script_path()
        if script_path:
            self.call_func_without_curses(
                lambda: edit_script(script_path, editor="vim")
            )

    def update_last_refresh_time(self):
        self.last_refresh_time = time.time()

    def _run_script_no_close(self):
        try:
            self._run_selected_script(close_on_exit=False)
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
                    w = EditVariableMenu(script)
                    if len(w.variables) > 0:
                        w.exec()
                return True
            else:
                return super().on_char(ch)
        finally:
            # Reset last refresh time when key press event is processed
            self.update_last_refresh_time()

    def on_enter_pressed(self):
        self._run_selected_script()
        self.clear_input(reset_selection=True)
        return True

    def on_idle(self):
        try_reload_scripts_autorun(self.script_manager.scripts_autorun)

    def on_item_selection_changed(self, script: Optional[Script]):
        if self.__auto_infer_cmdline_args:
            text = self.get_input()
            if script and text:
                match = script.match_pattern(text)
                if match:
                    self.__cmdline_args[:] = [match.group()]
                else:
                    self.__cmdline_args.clear()
            else:
                self.__cmdline_args.clear()

    def on_update_screen(self, item_y_max: int):
        height = self._height

        if not self.is_refreshing:
            preview: List[Tuple[str, str]] = []

            script = self.get_selected_item()
            if script is not None:
                default_script_config = get_default_script_config()

                # Command line args
                if self.__cmdline_args:
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
                cfg_preview_count = 0
                for name, value in script.cfg.items():
                    if value != default_script_config[name]:
                        preview.append(
                            (
                                "yellow",
                                ("cfg : " if cfg_preview_count == 0 else " " * 6)
                                + f"{name:<16} : {value}",
                            )
                        )
                        cfg_preview_count += 1

            # Scheduled script log preview
            if not self.__no_daemon:
                preview.extend(
                    [
                        ("blue", line)
                        for line in get_scheduled_script_log_preview(
                            self.script_manager
                        )
                    ]
                )

            # Draw preview
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
                lambda script=script: execute_script(
                    script,
                    cd=len(self.__cmdline_args) == 0,
                    no_daemon=self.__no_daemon,
                )
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


def _main():
    global script_server

    log_file = os.path.join(get_data_dir(), "MyScripts.log")
    setup_logger(log_to_stderr=False, log_file=log_file)

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-n",
        "--no-daemon",
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
    parser.add_argument(
        "--is-running",
        action="store_true",
        help="Is another instance running?",
    )
    parser.add_argument(
        "-q",
        "--quit",
        action="store_true",
        help="Quit after running any script.",
    )
    parser.add_argument(
        "--prompt",
        default=None,
        help="Specify custom prompt.",
    )
    parser.add_argument(
        "-o",
        "--out-to-file",
        type=str,
        default=None,
        help="Save script output to a file.",
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Specify input.",
    )
    parser.add_argument(
        "--args",
        nargs=argparse.REMAINDER,
        help="Command line arguments to pass to scripts.",
    )

    args = parser.parse_args()

    # Output if an instance is already running.
    if args.is_running:
        print(f"is_instance_running(): {is_instance_running()}")
        return

    input_text = args.input if (args.input != "r" or args.input != "run") else None

    # Check if the daemon should be started.
    start_daemon = True
    if is_instance_running():
        start_daemon = False
    if input_text:
        start_daemon = False
    logging.debug(f"start_daemon: {start_daemon}")
    logging.info("Python executable: %s" % sys.executable)

    # Check if we should run in tmux.
    should_run_in_tmux = args.tmux or (
        not is_in_tmux() and start_daemon and is_termux()
    )
    if should_run_in_tmux:
        tmux_exec = shutil.which("tmux")
        if tmux_exec is not None:
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

    no_daemon = args.no_daemon or bool(args.args) or bool(args.out_to_file)
    run_script_and_quit = (
        bool(args.input) or args.quit or bool(args.args) or bool(args.out_to_file)
    )
    while True:  # repeat if _MyScriptMenu throws exceptions
        try:
            _MyScriptMenu(
                cmdline_args=args.args,
                input_text=input_text,
                no_daemon=no_daemon,
                run_script_and_quit=run_script_and_quit,
                script_manager=script_manager,
                out_to_file=args.out_to_file,
                prompt=args.prompt,
            ).exec()
            if run_script_and_quit:
                break

        except Exception:
            traceback.print_exc(file=sys.stdout)
            pause()


if __name__ == "__main__":
    _main()
