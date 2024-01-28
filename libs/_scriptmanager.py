import bisect
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from typing import Callable, Dict, Iterator, List, Optional, Set, Tuple

from _script import (
    Script,
    execute_script_autorun,
    get_all_script_access_time,
    get_all_scripts,
    get_data_dir,
    get_my_script_root,
    get_script_history_file,
)
from _shutil import (
    clear_env_var_explorer,
    get_ahk_exe,
    load_json,
    pause,
    refresh_env_vars,
    save_json,
    start_process,
    update_env_var_explorer,
)
from _template import render_template_file
from _term import clear_terminal

MYSCRIPT_GLOBAL_HOTKEY = os.path.join(get_data_dir(), "GlobalHotkey.ahk")


def add_keyboard_hooks(keyboard_hooks):
    if sys.platform != "linux":
        import keyboard

        keyboard.unhook_all()
        for hotkey, func in keyboard_hooks.items():
            keyboard.add_hotkey(hotkey, func)


def register_global_hotkeys_linux(scripts: List[Script]):
    if not shutil.which("sxhkd"):
        logging.warning("sxhkd is not installed, skip global hotkey registration.")
        return

    s = (
        "control+q\n"
        "  wmctrl -a MyTerminal"
        f' || alacritty -e "{get_my_script_root()}/myscripts"\n\n'
    )

    for script in scripts:
        hotkey_chain = script.cfg["globalHotkey"]
        if hotkey_chain and script.is_supported():
            hotkey_def = ";".join(
                [
                    (
                        hotkey.lower()
                        .replace("win+", "super+")
                        .replace("enter", "Return")
                        .replace("[", "bracketleft")
                        .replace("]", "bracketright")
                    )
                    for hotkey in hotkey_chain.split()
                ]
            )
            s += "{}\n".format(hotkey_def)
            s += (
                "  python3"
                f" {get_my_script_root()}/bin/start_script.py"
                f" {script.script_path}\n\n"
            )

    with open(os.path.expanduser("~/.sxhkdrc"), "w") as f:
        f.write(s)
    subprocess.call(["pkill", "-USR1", "sxhkd"])
    start_process(["sxhkd", "-c", os.path.expanduser("~/.sxhkdrc")])


def _to_ahk_hotkey(hotkey: str):
    return (
        hotkey.lower()
        .replace("ctrl+", "^")
        .replace("alt+", "!")
        .replace("shift+", "+")
        .replace("win+", "#")
    )


def register_global_hotkeys_win(scripts: List[Script]):
    def wrap_hotkey_def_with_context_expr(hotkey_def: str, expr: str):
        return f"#If {expr}\n    {hotkey_def}\n#If\n\n"

    default_hotkey_context = 'not WinActive("ahk_exe vncviewer.exe")'
    hotkeys = ""
    match_clipboard = []
    first_hotkey_defined: Set[str] = set()

    for script in scripts:
        function_def = f'StartScript("{script.name}", "{script.script_path}")'
        hotkey_chain = script.cfg["globalHotkey"]
        if hotkey_chain and script.is_supported():
            hotkey_array = hotkey_chain.split()
            if len(hotkey_array) == 1:
                htk = _to_ahk_hotkey(hotkey_array[0])
                hotkeys += wrap_hotkey_def_with_context_expr(
                    f"{htk}::{function_def}", default_hotkey_context
                )
            elif len(hotkey_array) == 2:
                # First hotkey in the key combination
                key1 = _to_ahk_hotkey(hotkey_array[0])
                if key1 not in first_hotkey_defined:
                    hotkeys += wrap_hotkey_def_with_context_expr(
                        f"{key1}::return", default_hotkey_context
                    )

                first_hotkey_defined.add(key1)

                # Second hotkey in the key combination
                key2 = _to_ahk_hotkey(hotkey_array[1])
                hotkeys += wrap_hotkey_def_with_context_expr(
                    f"{key2}::{function_def}",
                    f'{default_hotkey_context} and A_PriorHotkey = "{key1}"',
                )

            else:
                raise Exception("Only support chaining two hotkeys.")

        mc = script.cfg["matchClipboard"]
        if mc:
            match_clipboard.append([mc, script.name, script.script_path])

    match_clipboard = sorted(match_clipboard, key=lambda x: x[1])  # sort by name

    render_template_file(
        os.path.join(get_my_script_root(), "GlobalHotkey.ahk"),
        MYSCRIPT_GLOBAL_HOTKEY,
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

    subprocess.Popen(
        [get_ahk_exe(), MYSCRIPT_GLOBAL_HOTKEY], close_fds=True, shell=True
    )


def execute_script(
    script: Script, args: Optional[List[str]] = None, close_on_exit=None, no_gui=False
):
    refresh_env_vars()

    args_: List[str]
    if args is None:
        if not no_gui:
            args_ = update_env_var_explorer()
        else:
            args_ = []
    else:
        args_ = args

    # Save last executed script
    save_json(get_script_history_file(), {"file": script.script_path, "args": args_})

    if not no_gui:
        clear_terminal()

    success = script.execute(
        args=args_,
        close_on_exit=close_on_exit,
        restart_instance=True,
        new_window=False if no_gui else None,
    )
    if not success:
        pause()


def register_global_hotkeys_mac(scripts: List[Script], no_gui=False):
    keyboard_hooks = {}
    for script in scripts:
        hotkey = script.cfg["globalHotkey"]
        if hotkey and script.is_supported():
            logging.info("GlobalHotkey: %s: %s" % (hotkey, script.name))
            keyboard_hooks[hotkey] = lambda script=script: execute_script(
                script, no_gui=no_gui
            )
    add_keyboard_hooks(keyboard_hooks)


def register_global_hotkeys(scripts, no_gui=False):
    if sys.platform == "win32":
        register_global_hotkeys_win(scripts)
    elif sys.platform == "linux":
        register_global_hotkeys_linux(scripts)
    elif sys.platform == "darwin":
        register_global_hotkeys_mac(scripts, no_gui=no_gui)


def _get_next_scheduled_script_run_time_file():
    return os.path.join(get_data_dir(), "next_scheduled_script_run_time.json")


class ScriptManager:
    def __init__(self, start_daemon=True, startup=False):
        self.next_scheduled_script_run_time: Dict[str, float] = load_json(
            _get_next_scheduled_script_run_time_file(), default={}
        )
        self.start_daemon = start_daemon
        self.scripts_autorun: List[Script] = []
        self.scripts: List[Script] = []
        self.startup = startup

        self.__match_scripts: List[Tuple[re.Pattern, Script]] = []
        self.__scheduled_script: List[Script] = []

    def update_script_access_time(self):
        access_time = get_all_script_access_time()
        for script in self.scripts:
            if script.script_path in access_time:
                script.mtime = max(
                    script.mtime,
                    access_time[script.script_path],
                )

    def sort_scripts(self):
        self.update_script_access_time()
        self.scripts[:] = sorted(
            self.scripts,
            key=lambda script: script.mtime,
            reverse=True,
        )

    def reload_scripts(
        self,
        autorun=True,
        on_progress: Optional[Callable[[], None]] = None,
    ) -> bool:
        script_dict = {script.script_path: script for script in self.scripts}
        self.scripts.clear()
        self.scripts_autorun.clear()
        self.__scheduled_script.clear()

        clear_env_var_explorer()

        any_script_reloaded = False
        for i, file in enumerate(get_all_scripts()):
            if i % 20 == 0:
                if on_progress is not None:
                    on_progress()

            if file in script_dict:
                script = script_dict[file]
                reloaded = script.refresh_script()
            else:
                script = Script(file)
                reloaded = True

            if script.cfg["runEveryNSec"]:
                self.__scheduled_script.append(script)

            if reloaded:
                any_script_reloaded = True
                should_run_script = False
                if script.cfg["autoRun"] and script.is_supported():
                    self.scripts_autorun.append(script)
                    if autorun:
                        should_run_script = True

                if script.cfg["runAtStartup"] and self.startup:
                    logging.info("runAtStartup: %s" % script.name)
                    should_run_script = True

                # Check if auto run script
                if should_run_script:
                    execute_script_autorun(script)

            bisect.insort(self.scripts, script)

        return any_script_reloaded

    def update_clipboard_script_map(self):
        self.__match_scripts.clear()
        for script in self.scripts:
            patt = script.cfg["matchClipboard"]
            if patt:
                self.__match_scripts.append((re.compile(patt), script))

    def match_clipboard(self, s: str) -> Iterator[Script]:
        for regex, script in self.__match_scripts:
            if re.search(regex, s):
                yield script

    def refresh_all_scripts(
        self,
        on_progress: Optional[Callable[[], None]] = None,
        on_register_hotkeys: Optional[Callable[[Dict[str, Script]], None]] = None,
    ):
        begin_time = time.time()

        if self.reload_scripts(autorun=self.start_daemon, on_progress=on_progress):
            # Register hotkeys
            if on_register_hotkeys is not None:
                hotkeys: Dict[str, Script] = {}
                for script in self.scripts:
                    hotkey = script.cfg["hotkey"]
                    if hotkey:
                        logging.debug("Hotkey: %s: %s" % (hotkey, script.name))
                        hotkeys[hotkey] = script
                on_register_hotkeys(hotkeys)

            if self.start_daemon:
                register_global_hotkeys(self.scripts)
                self.update_clipboard_script_map()

        self.sort_scripts()

        logging.debug("Script refresh takes %.1f secs." % (time.time() - begin_time))

        # Startup script should only be run once
        self.startup = False

    def get_scheduled_scripts_run_time(self) -> Dict[Script, float]:
        run_time: Dict[Script, float] = {}
        for script in self.__scheduled_script:
            if script.script_path in self.next_scheduled_script_run_time:
                run_time[script] = self.next_scheduled_script_run_time[
                    script.script_path
                ]
        return run_time

    def get_scheduled_scripts_to_run(self) -> Iterator[Script]:
        if not self.start_daemon:
            return

        has_any_script_to_run = False
        now = time.time()
        for script in self.__scheduled_script:
            run_every_n_seconds = script.cfg["runEveryNSec"]
            if run_every_n_seconds:
                if (
                    script.script_path not in self.next_scheduled_script_run_time
                    or now > self.next_scheduled_script_run_time[script.script_path]
                ):
                    if script.is_running():
                        logging.warn("Script is still running, skip scheduled task.")
                    else:
                        logging.info(f"Run scheduled task: {script.name}")
                        has_any_script_to_run = True
                        yield script

                    self.next_scheduled_script_run_time[
                        script.script_path
                    ] = time.time() + int(run_every_n_seconds)

        if has_any_script_to_run:
            # Save last scheduled script run time
            config_file = _get_next_scheduled_script_run_time_file()
            save_json(config_file, self.next_scheduled_script_run_time)
