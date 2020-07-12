import sys
import os
import curses
import curses.ascii
import re

sys.path.append(os.path.join(os.path.realpath(os.path.dirname(__file__)), "libs"))
sys.path.append(os.path.join(os.path.realpath(os.path.dirname(__file__)), "bin"))

import run_python
from _script import *


class Input:
    def __init__(self, label=""):
        self.text = ""
        self.label = label
        self.caret_pos = 0

    def on_update_screen(self, stdscr, row, cursor=False):
        stdscr.addstr(row, 0, self.label)

        text_start = len(self.label) + 1 if self.label else 0
        stdscr.addstr(row, text_start, self.text)

        if cursor:
            stdscr.move(row, self.caret_pos + text_start)

    def on_getch(self, ch):
        text_changed = False

        if ch == curses.ERR:
            pass
        elif ch == curses.KEY_LEFT:
            self.caret_pos = max(self.caret_pos - 1, 0)
        elif ch == curses.KEY_RIGHT:
            self.caret_pos = min(self.caret_pos + 1, len(self.text))
        elif ch == ord("\b"):
            self.text = self.text[: self.caret_pos - 1] + self.text[self.caret_pos :]
            self.caret_pos = max(self.caret_pos - 1, 0)
            text_changed = True
        elif ch == curses.ascii.ctrl(ord("a")):
            self.text = ""
            self.caret_pos = 0
            text_changed = True
        elif ch == ord("\n"):
            pass
        elif re.match("[\x00-\x7F]", chr(ch)):
            self.text = (
                self.text[: self.caret_pos] + chr(ch) + self.text[self.caret_pos :]
            )
            self.caret_pos += 1
            text_changed = True

        if text_changed:
            pass


def sort_scripts(scripts):
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


def search_items(items, kw):
    if not kw:
        for i, s in enumerate(items):
            yield i, s
    else:
        tokens = kw.split(" ")
        for i, item in enumerate(items):
            if all([(x in str(item).lower()) for x in tokens]):
                yield i, item


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


class SearchWindow:
    def __init__(self, stdscr, items):
        input_ = Input(">")
        self.items = items

        while True:
            height, width = stdscr.getmaxyx()

            # Search scripts
            matched_items = list(search_items(items, input_.text))

            # Sreen update
            stdscr.clear()

            # Get matched scripts
            row = 2
            max_row = height
            for i, (idx, item) in enumerate(matched_items):
                stdscr.addstr(row, 0, "%d. %s" % (idx + 1, str(item)))
                row += 1
                if row >= max_row:
                    break

            input_.on_update_screen(stdscr, 0, cursor=True)
            stdscr.refresh()

            # Keyboard event
            ch = stdscr.getch()

            if ch == ord("\n"):
                if len(matched_items) > 0:
                    _, item = matched_items[0]
                else:
                    item = None

                self.on_accept(input_.text, item)

            elif ch == curses.ascii.ctrl(ord("w")):
                return

            elif self.on_getch(ch):
                pass

            else:
                input_.on_getch(ch)

    def on_getch(self, ch):
        return False

    def on_accept(self, text, item):
        pass


scripts = []
modified_time = {}
last_ts = 0
hotkeys = {}
execute_script = None


def main(stdscr):
    global scripts
    global modified_time
    global last_ts
    global hotkeys
    global execute_script

    # # Clear screen
    # stdscr.clear()

    curses.noecho()
    curses.cbreak()
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    # stdscr = curses.initscr()
    stdscr.keypad(1)
    stdscr.nodelay(False)

    input_ = Input(">")

    while True:
        # Reload scripts
        now = time.time()
        if now - last_ts > 2.0:
            load_scripts(scripts, modified_time, autorun=False)
            scripts = sort_scripts(scripts)
            hotkeys = register_hotkeys(scripts)
        last_ts = now

        height, width = stdscr.getmaxyx()

        # Search scripts
        matched_scripts = list(search_items(scripts, input_.text))

        # Sreen update
        stdscr.clear()

        # Get matched scripts
        row = 2
        max_row = height
        for i, (idx, script) in enumerate(matched_scripts):
            stdscr.addstr(row, 0, "%d. %s" % (idx + 1, str(script)))
            row += 1

            if i == 0:
                vars = get_script_variables(script)
                if len(vars):
                    max_width = max([len(val_name) for val_name in vars]) + 1
                    max_row = max(5, height - len(vars))
                    for i, (var_name, var_val) in enumerate(vars.items()):
                        if max_row + i >= height:
                            break
                        stdscr.addstr(
                            max_row + i, 0, var_name.ljust(max_width) + ": " + var_val,
                        )

            if row >= max_row:
                break

        input_.on_update_screen(stdscr, 0, cursor=True)
        stdscr.refresh()

        # Keyboard event
        ch = stdscr.getch()

        if ch == ord("\n"):
            if matched_scripts:
                _, script = matched_scripts[0]

                update_script_acesss_time(script)

                execute_script = lambda: script.execute()
                return

        elif ch == curses.ascii.ctrl(ord("c")):
            return

        elif ch == curses.ascii.ctrl(ord("u")):
            if matched_scripts:
                _, script = matched_scripts[0]

                vars = get_script_variables(script)
                if len(vars):
                    max_width = max([len(val_name) for val_name in vars]) + 1
                    items = []
                    for i, (var_name, var_val) in enumerate(vars.items()):
                        items.append(var_name.ljust(max_width) + ": " + var_val)

                    SearchWindow(stdscr, items)

        elif ch in hotkeys:
            if matched_scripts:
                _, script = matched_scripts[0]
                script_abs_path = os.path.abspath(script.script_path)
                os.environ["_SCRIPT_PATH"] = script_abs_path

            execute_script = lambda: hotkeys[ch].execute()
            return

        else:
            input_.on_getch(ch)


if __name__ == "__main__":
    while True:
        curses.wrapper(main)
        if execute_script is not None:
            execute_script()
            execute_script = None
        else:
            break
