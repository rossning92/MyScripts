import curses
import curses.ascii
import threading
import time
import re
import signal
from _shutil import *


def activate_cur_terminal():
    if sys.platform == "win32":
        import ctypes

        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        ctypes.windll.user32.SetForegroundWindow(hwnd)


def minimize_cur_terminal():
    if sys.platform == "win32":
        import ctypes

        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        ctypes.windll.user32.ShowWindow(hwnd, 6)


def search(options):
    matched_indices = []

    while True:
        print2("> ", end="", color="green")
        kw = input()

        if kw.isdigit():
            try:
                idx = int(kw)
                return matched_indices[idx]
            except:
                print2("ERROR: invalid input.", color="red")

        else:
            matched_indices.clear()

            tokens = kw.split(" ")
            for i, s in enumerate(options):
                if all([(token in s) for token in tokens]):
                    matched_indices.append(i)

            for i, idx in enumerate(matched_indices):
                print("[%d] %s" % (i, options[idx]))


def _prompt(options, message=None):
    for i, option in enumerate(options):
        print("%d. %s" % (i + 1, option))

    if message is None:
        message = "selections"

    print("%s (indices, sep by space)> " % message, flush=True, end="")
    selections = input()
    selections = [int(x) - 1 for x in selections.split()]
    return selections


def prompt_checkbox(options, message=None):
    return _prompt(options=options, message=message)


def prompt_list(options, message=None):
    selected = _prompt(options=options, message=message)
    if len(selected) == 1:
        return selected[0]
    elif len(selected) == 0:
        return None
    else:
        raise Exception("Please only select 1 item.")


def search_items(items, kw):
    if not kw:
        for i, s in enumerate(items):
            yield i
    else:
        tokens = kw.split(" ")
        for i, item in enumerate(items):
            if all([(x in str(item).lower()) for x in tokens]):
                yield i


class InputWidget:
    def __init__(self, label="", text=""):
        self.label = label
        self.set_text(text)

    def set_text(self, text):
        self.text = text
        self.caret_pos = len(text)

    def on_update_screen(self, stdscr, row, cursor=False):
        stdscr.addstr(row, 0, self.label)

        text_start = len(self.label) + 1 if self.label else 0
        stdscr.attron(curses.color_pair(1))
        stdscr.addstr(row, text_start, self.text)
        stdscr.attroff(curses.color_pair(1))

        if cursor:
            try:
                stdscr.move(row, self.caret_pos + text_start)
            except:
                pass

    def clear(self):
        self.text = ""
        self.caret_pos = 0

    def on_char(self, ch):
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


class Menu:
    def __init__(self, stdscr=None, items=[], label=">", text=""):
        self.input_ = InputWidget(label=label, text=text)
        self.items = items
        self.closed = False
        self.matched_item_indices = []
        self.selected_row = 0
        self.width = -1
        self.height = -1
        self.stdscr = stdscr

        self.exec()

    def exec(self):
        if self.stdscr is None:
            curses.wrapper(self.main_loop_wrapped)
        else:
            self.exec_()

    def main_loop_wrapped(self, stdscr):
        self.stdscr = stdscr
        init_curses(stdscr)
        self.exec_()

    def exec_(self):
        self.on_main_loop()
        last_input = None
        while True:
            self.height, self.width = self.stdscr.getmaxyx()

            if last_input != self.get_text():
                last_input = self.get_text()

                # Search scripts
                self.matched_item_indices = list(
                    search_items(self.items, self.get_text())
                )

                self.selected_row = 0

            # Sreen update
            self.stdscr.clear()
            self.on_update_screen()
            self.stdscr.refresh()

            # Keyboard event
            ch = self.stdscr.getch()

            if ch == -1:  # getch() timeout
                pass

            elif self.on_char(ch):
                pass

            elif ch == ord("\n"):
                self.on_enter_pressed()

            elif ch == curses.KEY_UP:
                self.selected_row = max(self.selected_row - 1, 0)
                self.on_item_selected()

            elif ch == curses.KEY_DOWN:
                self.selected_row = min(
                    self.selected_row + 1, len(self.matched_item_indices) - 1
                )
                self.on_item_selected()

            elif ch == curses.ascii.ESC:
                return

            elif ch != 0:
                self.input_.on_char(ch)

            if self.closed:
                return

            self.on_main_loop()

    def get_selected_index(self):
        if len(self.matched_item_indices) > 0:
            return self.matched_item_indices[self.selected_row]
        else:
            return -1

    def get_text(self):
        return self.input_.text

    def on_update_screen(self):
        # Get matched scripts
        row = 2
        for i, item_index in enumerate(self.matched_item_indices):
            if self.selected_row == i:  # Hightlight on
                self.stdscr.attron(curses.color_pair(2))
            s = "%d. %s" % (item_index + 1, str(self.items[item_index]))
            try:
                self.stdscr.addstr(row, 0, s)
            except curses.error:
                pass
            if self.selected_row == i:  # Highlight off
                self.stdscr.attroff(curses.color_pair(2))

            row += 1
            if row >= self.height:
                break

        self.input_.on_update_screen(self.stdscr, 0, cursor=True)

    def get_selected_item(self):
        if len(self.matched_item_indices) > 0:
            item_index = self.matched_item_indices[self.selected_row]
            return self.items[item_index]
        else:
            return None

    def on_char(self, ch):
        return False

    def on_enter_pressed(self):
        self.close()

    def on_tab_pressed(self):
        pass

    def on_main_loop(self):
        pass

    def close(self):
        self.closed = True

    def on_item_selected(self):
        pass


def init_curses(stdscr):
    curses.noecho()
    curses.cbreak()
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
    stdscr.keypad(1)
    stdscr.nodelay(False)
    stdscr.timeout(1000)
