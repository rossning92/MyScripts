import argparse
import curses
import logging
import os
import platform
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
from typing import Callable, Dict, List, Optional, Tuple

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
    get_all_script_access_time,
    get_all_variables,
    get_data_dir,
    get_hotkey_abbr,
    get_script_history_file,
    get_script_variables,
    is_instance_running,
    reload_scripts,
    run_script,
    save_variables,
    setup_env_var,
    try_reload_scripts_autorun,
    update_script_access_time,
)
from _scriptserver import ScriptServer
from _shutil import (
    append_to_path_global,
    get_ahk_exe,
    getch,
    quote_arg,
    refresh_env_vars,
    run_at_startup,
    save_json,
    set_clip,
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
        self.enter_pressed = False

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
        self.enter_pressed = True
        self.close()

    def on_char(self, ch):
        if ch == ord("\t"):
            val = self.get_selected_item()
            if val is not None:
                self.input_.set_text(val)
            return True
        elif ch == curses.KEY_DC:  # delete key
            i = self.get_selected_index()
            del self.vars[self.var_name][i]
            save_variables(self.vars)
            return True

        return False


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


class VariableWindow(Menu):
    def __init__(self, script: Script):
        super().__init__(label=f"{script.name}> vars")
        self.variables = get_all_variables()
        self.variable_names = sorted(script.get_variable_names())
        self.variable_prefix = script.get_public_variable_prefix()
        self.enter_pressed = False

        if len(self.variable_names) > 0:
            self.update_items()

    def update_items(self):
        self.items[:] = format_variables(
            self.variables, self.variable_names, self.variable_prefix
        )

    def on_enter_pressed(self):
        self.enter_pressed = True
        self.close()

    def on_char(self, ch):
        if ch == ord("\t"):
            self.edit_variable()
            return True
        if ch == ord("C"):
            index = self.get_selected_index()
            name = self.variable_names[index]
            if name in self.variables and len(self.variables[name]) > 0:
                val = self.variables[name][0]
                set_clip(val)
                self.close()
            return True
        return False

    def edit_variable(self):
        index = self.get_selected_index()
        var_name = self.variable_names[index]
        w = VariableEditWindow(self.variables, var_name)
        w.exec()
        # if w.enter_pressed:
        #     self.close()
        self.update_items()
        self.input_.clear()


class ScriptManager:
    def __init__(self, no_gui=False, startup=False):
        self.scripts: List[Script] = []
        self.scripts_autorun: List[Script] = []
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

    def refresh_all_scripts(self, on_progress: Optional[Callable[[], None]] = None):
        begin_time = time.time()

        if reload_scripts(
            self.scripts,
            autorun=not self.no_gui,
            startup=self.startup,
            on_progress=on_progress,
            scripts_autorun=self.scripts_autorun,
        ):
            self.hotkeys = register_hotkeys(self.scripts)
            if not self.no_gui:
                register_global_hotkeys(self.scripts)
                monitor_clipboard(self.scripts)

        self.sort_scripts()

        logging.info("Script refresh takes %.1f secs." % (time.time() - begin_time))

        # Startup script should only be run once
        self.startup = False


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
        if sys.platform == "linux":
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
        f'  wmctrl -a MyScriptsTerminal || x-terminal-emulator -e "{MYSCRIPT_ROOT}/myscripts" --startup\n'
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
            s += f"  python3 {MYSCRIPT_ROOT}/bin/start_script.py {script.script_path}\n\n"

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
        os.path.join(MYSCRIPT_ROOT, "GlobalHotkey.ahk"),
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


class InternalHotkey:
    def __init__(self, hotkey: str, func: Callable):
        self.hotkey = hotkey
        self.func = func

    def __str__(self) -> str:
        return "%s (%s)" % (self.func.__name__, get_hotkey_abbr(self.hotkey))


def restart_program():
    os.execl(
        sys.executable,
        sys.executable,
        *(x for x in sys.argv if x != "--startup"),
    )


class MainWindow(Menu[Script]):
    def __init__(self, no_gui=None):
        self.no_gui = no_gui
        self.last_refresh_time = 0.0
        self.is_refreshing = False

        super().__init__(
            items=script_manager.scripts,
            ascii_only=True,
            cancellable=False,
            label=platform.node(),
        )

        self.internal_hotkeys: Dict[str, InternalHotkey] = {}
        self.add_internal_hotkey("ctrl+r", self._reload_scripts)
        self.add_internal_hotkey("shift+m", self._edit_script_config)
        self.add_internal_hotkey("shift+c", self._copy_to_clipboard)
        self.add_internal_hotkey("shift+i", self._copy_to_clipboard_include_derivative)
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
            and now - self.last_refresh_time > REFRESH_INTERVAL_SECS
        ):
            self._reload_scripts()

    def run_selected_script(self, close_on_exit=None):
        index = self.get_selected_index()
        if index >= 0:
            script = self.items[index]

            update_script_access_time(script)
            script_manager.sort_scripts()

            self.run_cmd(
                lambda: execute_script(
                    script,
                    close_on_exit=close_on_exit,
                    no_gui=self.no_gui,
                )
            )
            if script.cfg["reloadScriptsAfterRun"]:
                logging.info("Reload scripts after running: %s" % script.name)
                self._reload_scripts()

    def get_selected_script(self):
        index = self.get_selected_index()
        if index >= 0:
            return self.items[index]

    def get_selected_script_path(self):
        index = self.get_selected_index()
        if index >= 0:
            return self.items[index].script_path

    def _reload_scripts(self):
        if self.is_refreshing:
            return

        self.is_refreshing = True
        self.set_message("(refreshing scripts...)")

        def on_process():
            nonlocal self
            self.process_events(blocking=False)
            self.set_message("(refreshing scripts: %d)" % len(script_manager.scripts))

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
                f"(copied to clipboard: {content})"
                if content
                else "Copied to clipboard."
            )

    def _copy_to_clipboard_include_derivative(self):
        script = self.get_selected_script()
        if script:
            content = copy_script_path_to_clipboard(
                script, format="include", with_variables=True
            )
            self.set_message(f"(copied to clipboard: {content})")

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

    def _rename_script(self):
        script_path = self.get_selected_script_path()
        if script_path:
            self.set_message("(searching scripts to rename...)")
            if rename_script(
                script_path,
                on_progress=lambda msg: (
                    self.process_events(blocking=False),
                    self.set_message(msg),
                ),
            ):
                self._reload_scripts()
            self.set_message()
        self.clear_input()

    def _edit_script(self):
        script_path = self.get_selected_script_path()
        if script_path:
            self.run_cmd(lambda: edit_myscript_script(script_path))

    def _help(self):
        items: List[InternalHotkey] = []
        items.extend(self.internal_hotkeys.values())
        items.extend(script_manager.hotkeys.values())
        w = Menu(label="all hotkeys", items=items)
        w.exec()

    def update_last_refresh_time(self):
        self.last_refresh_time = time.time()

    def clear_input(self):
        self.input_.clear()
        self.reset_selection()

    def on_char(self, ch):
        ALT_KEY = 27
        self.set_message(None)

        try:
            if ch in self.internal_hotkeys:
                self.internal_hotkeys[ch].func()
                return True

            elif ch == KEY_CODE_CTRL_ENTER_WIN or (
                self.prev_key == ALT_KEY and ch == ord("\n")
            ):
                self.run_selected_script(close_on_exit=False)
                self.clear_input()
                return True

            elif ch == ord("\n"):
                self.run_selected_script()
                self.clear_input()
                return True

            elif ch == curses.ascii.ctrl(ord("c")):
                sys.exit(0)

            elif ch == ord("\t"):
                script = self.get_selected_item()
                if script is not None:
                    w = VariableWindow(script)
                    if w.variable_names:
                        w.exec()
                        if w.enter_pressed:
                            self.run_selected_script()
                return True

            elif ch == ord("L"):
                self.run_cmd(lambda: restart_program())

            elif ch in script_manager.hotkeys:
                script = script_manager.hotkeys[ch]
                selected_script = self.get_selected_item()
                if selected_script is not None:
                    os.environ["SCRIPT"] = os.path.abspath(selected_script.script_path)

                    self.run_cmd(lambda: execute_script(script, no_gui=self.no_gui))
                    if script.cfg["reloadScriptsAfterRun"]:
                        logging.info("Reload scripts after running: %s" % script.name)
                        self._reload_scripts()
                    else:
                        script_manager.sort_scripts()
                    return True

            return False
        finally:
            # Reset last refresh time when key press event is processed
            self.update_last_refresh_time()

    def on_idle(self):
        try_reload_scripts_autorun(script_manager.scripts_autorun)

    def on_update_screen(self):
        height = self.height

        if not self.is_refreshing:
            script = self.get_selected_item()
            if script is not None:
                preview = []

                # Preview cmdline
                cmdline = script.cfg["cmdline"]
                if cmdline:
                    preview.append("---")
                    preview.append(cmdline)
                    preview.append("---")

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
                    if height + i >= self.height:
                        break
                    self.print_str(height + i, 0, s)

        super().on_update_screen(max_height=height)


def init(no_gui=False):
    if not no_gui and is_instance_running():
        logging.warning("An instance is already running, exiting.")
        sys.exit(0)

    logging.info("Python executable: %s" % sys.executable)

    # Add bin folder to PATH
    bin_dir = os.path.join(MYSCRIPT_ROOT, "bin")
    append_to_path_global(bin_dir)

    user_site = subprocess.check_output(
        [sys.executable, "-m", "site", "--user-site"], universal_newlines=True
    ).strip()
    script_dir = os.path.abspath(os.path.join(user_site, "..", "Scripts"))
    append_to_path_global(script_dir)

    setup_env_var(os.environ)

    refresh_env_vars()

    setup_nodejs(install=False)

    if not no_gui:
        script_server = ScriptServer()
        script_server.start_server()


def main_loop(no_gui=None, quit=False):
    while True:
        try:
            MainWindow(no_gui=no_gui).exec()

            if quit:
                break

            # HACK: workaround: key bindings will not work on windows.
            # time.sleep(1)

        except Exception:
            traceback.print_exc(file=sys.stdout)
            input("Press any key to retry...")


if __name__ == "__main__":
    setup_logger(
        log_file=os.path.join(get_data_dir(), "MyScripts.log"),
        log_to_stdout=False,
        level=logging.DEBUG,
    )

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
        cmdline=quote_arg(os.path.join(MYSCRIPT_ROOT, "myscripts.cmd")) + " --startup",
    )

    # setup_console_font()
    init(no_gui=args.no_gui)
    script_manager = ScriptManager(no_gui=args.no_gui, startup=args.startup)
    main_loop(no_gui=args.no_gui, quit=args.quit)
