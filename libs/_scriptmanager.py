import bisect
import curses
import logging
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from typing import Callable, Dict, List, Optional, Tuple

from _script import (
    Script,
    execute_script_autorun,
    get_all_script_access_time,
    get_all_scripts,
    get_data_dir,
    get_my_script_root,
    get_script_history_file,
    run_script,
)
from _shutil import (
    clear_env_var_explorer,
    get_ahk_exe,
    getch,
    is_in_termux,
    refresh_env_vars,
    save_json,
    start_process,
    update_env_var_explorer,
)
from _template import render_template_file

GLOBAL_HOTKEY = os.path.join(get_data_dir(), "GlobalHotkey.ahk")


def add_keyboard_hooks(keyboard_hooks):
    if sys.platform != "linux":
        import keyboard

        keyboard.unhook_all()
        for hotkey, func in keyboard_hooks.items():
            keyboard.add_hotkey(hotkey, func)


class MonitorClipboardThread(threading.Thread):
    def __init__(self, match_clipboard: List[Tuple[re.Pattern, str, str]]):
        super().__init__(daemon=True)

        self.match_clipboard = match_clipboard
        self.stopped = threading.Event()

    def run(self) -> None:
        logging.debug("MonitorClipboardThread started.")
        if sys.platform == "linux" and not is_in_termux():
            import pyperclip

            try:
                while not self.stopped.is_set():
                    try:
                        clip = pyperclip.waitForNewPaste(timeout=0.5)

                        matched_script: Dict[str, str] = {}
                        for patt, script_name, script_path in self.match_clipboard:
                            if re.match(patt, clip):
                                matched_script[script_name] = script_path

                        if matched_script:
                            ps = subprocess.run(
                                ["dmenu"],
                                input="\n".join(matched_script.keys()),
                                encoding="utf-8",
                                stdout=subprocess.PIPE,
                            )
                            script_name = ps.stdout.strip()
                            if script_name in matched_script:
                                script_path = matched_script[script_name]
                                run_script(script_path, args=[clip], new_window=None)

                    except pyperclip.PyperclipTimeoutException:
                        pass
            except Exception as ex:
                logging.error("Error on monitoring clipboard: %s" % ex)

        logging.debug("MonitorClipboardThread stopped.")

    def stop(self):
        if self.stopped.is_set():
            raise Exception("Must not call stop twice.")
        self.stopped.set()
        self.join()


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


_monitor_clipboard_thread: Optional[MonitorClipboardThread] = None


def monitor_clipboard(scripts: List[Script]):
    match_clipboard: List[Tuple[re.Pattern, str, str]] = []
    for script in scripts:
        patt = script.cfg["matchClipboard"]
        if patt:
            match_clipboard.append((re.compile(patt), script.name, script.script_path))
    match_clipboard = sorted(match_clipboard, key=lambda x: x[1])  # sort by name

    # Start MonitorClipboardThread
    global _monitor_clipboard_thread
    if _monitor_clipboard_thread is not None:
        _monitor_clipboard_thread.stop()

    _monitor_clipboard_thread = MonitorClipboardThread(match_clipboard=match_clipboard)
    _monitor_clipboard_thread.start()


def register_global_hotkeys_linux(scripts: List[Script]):
    if not shutil.which("sxhkd"):
        logging.warning("sxhkd is not installed, skip global hotkey registration.")
        return

    s = (
        f"control+q\n"
        f'  wmctrl -a MyScriptsTerminal || x-terminal-emulator -e "{get_my_script_root()}/myscripts" --startup\n'
        "\n"
    )

    for script in scripts:
        hotkey = script.cfg["globalHotkey"]

        if hotkey:
            hotkey = (
                hotkey.lower()
                .replace("win+", "super+")
                .replace("enter", "Return")
                .replace("[", "bracketleft")
                .replace("]", "bracketright")
            )
            s += "{}\n".format(hotkey)
            s += f"  python3 {get_my_script_root()}/bin/start_script.py {script.script_path}\n\n"

    with open(os.path.expanduser("~/.sxhkdrc"), "w") as f:
        f.write(s)
    subprocess.call(["pkill", "-USR1", "sxhkd"])
    start_process(["sxhkd", "-c", os.path.expanduser("~/.sxhkdrc")])


def register_global_hotkeys_win(scripts: List[Script]):
    hotkeys = ""
    match_clipboard = []

    for script in scripts:
        hotkey = script.cfg["globalHotkey"]
        if hotkey:
            if hotkey:
                hotkey = hotkey.lower()
                hotkey = hotkey.replace("ctrl+", "^")
                hotkey = hotkey.replace("alt+", "!")
                hotkey = hotkey.replace("shift+", "+")
                hotkey = hotkey.replace("win+", "#")
                hotkeys += (
                    f'{hotkey}::StartScript("{script.name}", "{script.script_path}")\n'
                )
        mc = script.cfg["matchClipboard"]
        if mc:
            match_clipboard.append([mc, script.name, script.script_path])

    match_clipboard = sorted(match_clipboard, key=lambda x: x[1])  # sort by name

    render_template_file(
        os.path.join(get_my_script_root(), "GlobalHotkey.ahk"),
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


def execute_script(script: Script, close_on_exit=None, no_gui=False):
    refresh_env_vars()
    if no_gui:
        args = None
    else:
        args = update_env_var_explorer()

    # Save last executed script
    save_json(get_script_history_file(), {"file": script.script_path, "args": args})

    success = script.execute(
        args=args,
        close_on_exit=close_on_exit,
        restart_instance=True,
        new_window=False if no_gui else None,
    )
    if not success:
        print("(press any key to continue...)")
        getch()


def register_global_hotkeys_mac(scripts: List[Script], no_gui=False):
    keyboard_hooks = {}
    for script in scripts:
        hotkey = script.cfg["globalHotkey"]
        if hotkey:
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


class ScriptManager:
    def __init__(self, no_gui=False, startup=False):
        self.scripts: List[Script] = []
        self.scripts_autorun: List[Script] = []
        self.scripts_scheduled: List[Script] = []
        self.hotkeys: Dict[str, Script] = {}
        self.no_gui = no_gui
        self.startup = startup

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

    def reload_scripts(
        self,
        autorun=True,
        on_progress: Optional[Callable[[], None]] = None,
    ) -> bool:
        script_dict = {script.script_path: script for script in self.scripts}
        self.scripts.clear()
        self.scripts_autorun.clear()
        self.scripts_scheduled.clear()
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

            if script.cfg["runEveryNSeconds"]:
                self.scripts_scheduled.append(script)

            if reloaded:
                any_script_reloaded = True
                should_run_script = False
                if script.cfg["autoRun"]:
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

    def refresh_all_scripts(self, on_progress: Optional[Callable[[], None]] = None):
        begin_time = time.time()

        if self.reload_scripts(autorun=not self.no_gui, on_progress=on_progress):
            self.hotkeys = register_hotkeys(self.scripts)
            if not self.no_gui:
                register_global_hotkeys(self.scripts)
                monitor_clipboard(self.scripts)

        self.sort_scripts()

        logging.info("Script refresh takes %.1f secs." % (time.time() - begin_time))

        # Startup script should only be run once
        self.startup = False

    def check_scheduled_scripts(self):
        now = time.time()
        for script in self.scripts_scheduled:
            run_every_n_seconds = script.cfg["runEveryNSeconds"]
            if run_every_n_seconds:
                if now > script.last_scheduled_run_time + int(run_every_n_seconds):
                    logging.info(f"Run scheduled script: {script.name}")
                    script.execute(
                        args=[],
                        close_on_exit=True,
                        restart_instance=False,
                        new_window=False,
                        background=True,
                    )
                    script.last_scheduled_run_time = now
