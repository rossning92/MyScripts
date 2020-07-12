import sys
import os
import curses
import curses.ascii
import re
import time

sys.path.append(os.path.join(os.path.realpath(os.path.dirname(__file__)), "libs"))
sys.path.append(os.path.join(os.path.realpath(os.path.dirname(__file__)), "bin"))

import run_python
from _script import *


class Input:
    def __init__(self, label="", text=""):
        self.text = text
        self.label = label
        self.caret_pos = len(text)

    def on_update_screen(self, stdscr, row, cursor=False):
        stdscr.addstr(row, 0, self.label)

        text_start = len(self.label) + 1 if self.label else 0
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(row, text_start, self.text)
        stdscr.attroff(curses.color_pair(1))

        if cursor:
            stdscr.move(row, self.caret_pos + text_start)

    def clear(self):
        self.text = ""
        self.caret_pos = 0

    def on_getch(self, ch):
        if ch == curses.ERR:
            pass
        elif ch == curses.KEY_LEFT:
            self.caret_pos = max(self.caret_pos - 1, 0)
        elif ch == curses.KEY_RIGHT:
            self.caret_pos = min(self.caret_pos + 1, len(self.text))
        elif ch == ord("\b"):
            self.text = self.text[: self.caret_pos - 1] + self.text[self.caret_pos :]
            self.caret_pos = max(self.caret_pos - 1, 0)
        elif ch == curses.ascii.ctrl(ord("a")):
            self.clear()
        elif ch == ord("\n"):
            pass
        elif re.match("[\x00-\x7F]", chr(ch)):
            self.text = (
                self.text[: self.caret_pos] + chr(ch) + self.text[self.caret_pos :]
            )
            self.caret_pos += 1


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
    def __init__(self, stdscr, items, label=">", text=""):
        self.input_ = Input(label=label, text=text)
        self.items = items
        self.closed = False
        self.stdscr = stdscr

        while True:
            height, width = stdscr.getmaxyx()

            # Search scripts
            matched_items = list(search_items(items, self.input_.text))

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

            self.input_.on_update_screen(stdscr, 0, cursor=True)
            stdscr.refresh()

            # Keyboard event
            ch = stdscr.getch()

            if ch == ord("\n") or ch == ord("\t"):
                if len(matched_items) > 0:
                    item_index, item = matched_items[0]
                else:
                    item = None
                    item_index = -1

                if ch == ord("\n"):
                    self.on_enter_pressed(self.input_.text, item_index)
                else:
                    self.on_tab_pressed(self.input_.text, item_index)

            elif ch == 27:
                return

            elif self.on_getch(ch):
                pass

            else:
                self.input_.on_getch(ch)

            if self.closed:
                return

    def on_getch(self, ch):
        return False

    def on_enter_pressed(self, text, item_index):
        pass

    def on_tab_pressed(self, text, item_index):
        pass

    def close(self):
        self.closed = True


class VariableEditWindow(SearchWindow):
    def __init__(self, stdscr, vars, var_name):
        self.vars = vars
        self.var_name = var_name

        super().__init__(stdscr, [], label=var_name + " :", text=self.vars[var_name])

    def on_enter_pressed(self, text, item_index):
        self.vars[self.var_name] = text
        self.close()


class VariableSearchWindow(SearchWindow):
    def __init__(self, stdscr, script):
        self.vars = get_script_variables(script)
        self.items = []

        if len(self.vars):
            self.update_items()
            super().__init__(stdscr, self.items, label="%s >" % (script.name))

    def update_items(self):
        self.items.clear()
        max_width = max([len(val_name) for val_name in self.vars]) + 1
        for _, (var_name, var_val) in enumerate(self.vars.items()):
            self.items.append(var_name.ljust(max_width) + ": " + var_val)

    def on_getch(self, ch):
        if ch == ord("\t"):
            self.close()
        else:
            super().on_getch(ch)

    def on_enter_pressed(self, text, item_index):
        var_name = list(self.vars)[item_index]
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


def main(stdscr):
    # # Clear screen
    # stdscr.clear()

    curses.noecho()
    curses.cbreak()
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    stdscr = curses.initscr()
    stdscr.keypad(1)
    stdscr.nodelay(False)

    input_ = Input(">")

    while True:
        # Reload scripts
        now = time.time()
        if now - state.last_ts > 2.0:
            load_scripts(state.scripts, state.modified_time, autorun=False)
            state.scripts = sort_scripts(state.scripts)
            state.hotkeys = register_hotkeys(state.scripts)
        state.last_ts = now

        height, width = stdscr.getmaxyx()

        # Search scripts
        matched_scripts = list(search_items(state.scripts, input_.text))

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

                state.execute_script = lambda: script.execute()
                return

        elif ch == 27:
            pass

        elif ch == curses.ascii.ctrl(ord("c")):
            return

        elif ch == ord("\t"):
            if matched_scripts:
                _, script = matched_scripts[0]

                VariableSearchWindow(stdscr, script)

        elif ch in state.hotkeys:
            if matched_scripts:
                _, script = matched_scripts[0]
                script_abs_path = os.path.abspath(script.script_path)
                os.environ["_SCRIPT_PATH"] = script_abs_path

            state.execute_script = lambda: state.hotkeys[ch].execute()
            return

        elif ch != 0:
            input_.on_getch(ch)


if __name__ == "__main__":
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
