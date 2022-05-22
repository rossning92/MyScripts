import ctypes
import curses
import curses.ascii
import locale
import os
import re
import sys
import time

from _shutil import load_json, save_json


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


def set_term_title(title):
    if sys.platform == "win32":
        title = title.encode(locale.getpreferredencoding())
        ctypes.windll.kernel32.SetConsoleTitleA(title)


def _select_options_ncurse(options, save_history=False):
    if save_history:
        history = load_json("search_history.json", [])
        sort_key = {x: i for i, x in enumerate(history)}
        options, indices = zip(
            *sorted(
                zip(options, list(range(len(options)))),
                key=lambda x: sort_key[x[0]] if x[0] in sort_key else sys.maxsize,
            )
        )

    w = Menu(items=options)
    idx = w.exec()

    if save_history:
        if idx >= 0:
            try:
                history.remove(options[idx])
            except ValueError:
                pass
            history.insert(0, options[idx])
            save_json("search_history.json", history)
        idx = indices[idx]

    return idx


def select_option(options, save_history=False):
    return _select_options_ncurse(options, save_history=save_history)


def _prompt(options, message=None):
    for i, option in enumerate(options):
        print("%d. %s" % (i + 1, option))

    if message is None:
        message = "selections"

    print("%s (indices, sep by space)> " % message, flush=True, end="")
    selections = input()
    selections = [int(x) - 1 for x in selections.split()]
    return selections


def select_options(options, message=None):
    return _prompt(options=options, message=message)


def prompt_list(options, message=None):
    selected = _prompt(options=options, message=message)
    if len(selected) == 1:
        return selected[0]
    elif len(selected) == 0:
        return None
    else:
        raise Exception("Please only select 1 item.")


def _fuzzy_search_func(items, kw):
    if not kw:
        for i, s in enumerate(items):
            yield i
    else:
        for i, item in enumerate(items):
            if all([(x in str(item).lower()) for x in kw.split(" ")]):
                yield i


class InputWidget:
    def __init__(self, label="", text="", ascii_only=False):
        self.label = label
        self.set_text(text)
        self.ascii_only = ascii_only

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
        elif ch == curses.KEY_BACKSPACE or ch == ord("\b"):  # windows
            self.text = self.text[: self.caret_pos - 1] + self.text[self.caret_pos :]
            self.caret_pos = max(self.caret_pos - 1, 0)
        elif ch == curses.ascii.ctrl(ord("a")):
            self.clear()
        elif ch == ord("\n"):
            pass
        else:
            if not self.ascii_only or (
                self.ascii_only and re.match("[\x00-\x7F]", chr(ch))
            ):
                self.text = (
                    self.text[: self.caret_pos] + chr(ch) + self.text[self.caret_pos :]
                )
                self.caret_pos += 1


class Menu:
    def __init__(
        self,
        items=[],
        stdscr=None,
        label=">",
        text="",
        ascii_only=False,
        cancellable=True,
    ):
        self.input_ = InputWidget(label=label, text=text, ascii_only=ascii_only)
        self.items = items
        self.on_items = []
        self.closed = False
        self.matched_item_indices = []
        self.selected_row = 0
        self.width = -1
        self.height = -1
        self.stdscr = stdscr
        self.message = None
        self.cancellable = cancellable

    def item(self, name=None):
        def decorator(func):
            nonlocal name
            if name is None:
                name = func.__name__

            self.items.append(name)
            self.on_items.append(func)

            return func

        return decorator

    def exec(self) -> int:
        if self.stdscr is None:
            curses.wrapper(self.main_loop_wrapped)
        else:
            self.exec_()
        return self.get_selected_index()

    def main_loop_wrapped(self, stdscr):
        self.stdscr = stdscr
        init_curses(stdscr)
        self.exec_()
        self.stdscr = None

    def update_screen(self):
        self.height, self.width = self.stdscr.getmaxyx()

        if sys.platform == "win32":
            self.stdscr.clear()
        else:
            # Use erase instead of clear to prevent flickering
            self.stdscr.erase()
        self.on_update_screen()
        self.stdscr.refresh()

    def exec_(self):
        self.on_main_loop()
        last_input = None
        while True:
            if last_input != self.get_text():
                last_input = self.get_text()

                # Search scripts
                self.matched_item_indices = list(
                    _fuzzy_search_func(self.items, self.get_text())
                )

                self.selected_row = 0

            self.update_screen()

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

            elif ch == curses.KEY_PPAGE:
                self.selected_row = max(
                    self.selected_row - self.get_items_per_page(), 0
                )
                self.on_item_selected()

            elif ch == curses.KEY_NPAGE:
                self.selected_row = min(
                    self.selected_row + self.get_items_per_page(),
                    len(self.matched_item_indices) - 1,
                )
                self.on_item_selected()

            elif ch == curses.ascii.ESC:
                self.input_.clear()
                if self.cancellable:
                    self.matched_item_indices.clear()
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

    def get_items_per_page(self):
        return self.height - 2

    def on_update_screen(self):
        # Get matched scripts
        row = 2
        items_per_page = self.get_items_per_page()

        page = self.selected_row // items_per_page
        selected_index_in_page = self.selected_row % items_per_page
        indices_in_page = self.matched_item_indices[page * items_per_page :]
        for i, item_index in enumerate(indices_in_page):
            if i == selected_index_in_page:  # Hightlight on
                self.stdscr.attron(curses.color_pair(2))
            s = "{}  {}".format(item_index + 1, self.items[item_index])
            try:
                self.stdscr.addstr(row, 0, s)
            except curses.error:
                pass
            if i == selected_index_in_page:  # Highlight off
                self.stdscr.attroff(curses.color_pair(2))

            row += 1
            if row >= self.height:
                break

        self.input_.on_update_screen(self.stdscr, 0, cursor=True)

        if self.message is not None:
            self.stdscr.attron(curses.color_pair(3))
            self.stdscr.addstr(0, 0, self.message)
            self.stdscr.attroff(curses.color_pair(3))

    def get_selected_text(self):
        if len(self.matched_item_indices) > 0:
            item_index = self.matched_item_indices[self.selected_row]
            return self.items[item_index]
        else:
            return None

    def on_char(self, ch):
        if ch == ord("\t"):
            val = self.get_selected_text()
            if val is not None:
                self.input_.set_text(val)
            return True
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

    def loop(self):
        while True:
            self.closed = False
            self.exec()

            idx = self.get_selected_index()
            if idx < 0:
                break

            if idx >= 0 and idx < len(self.on_items):
                self.on_items[idx]()

            time.sleep(1)

    def set_message(self, message):
        self.message = message
        self.update_screen()


class DictValueEditWindow(Menu):
    def __init__(self, stdscr, dict_, name, type, default_vals=[]):
        self.dict_ = dict_
        self.name = name
        self.type = type

        super().__init__(
            items=default_vals, stdscr=stdscr, label=name + ":", text="",
        )

    def on_enter_pressed(self):
        val = self.get_text()
        if self.type == str:
            val = val.strip()
        elif self.type == int:
            val = int(val)
        elif self.type == float:
            val = float(val)
        elif self.type == bool:
            if val.lower() == "true":
                val = True
            elif val.lower() == "false":
                val = False
            elif val == "1":
                val = True
            elif val == "0":
                val = False
            else:
                raise Exception("Unknown bool value: {}".format(val))
        else:
            raise Exception("Unknown type: {}".format(self.type))

        self.dict_[self.name] = val

        self.close()

    def on_char(self, ch):
        if ch == ord("\t"):
            val = self.get_selected_text()
            if val is not None:
                self.input_.set_text(val)
            return True

        return False


class DictEditWindow(Menu):
    def __init__(self, dict_, default_dict=None, on_dict_update=None):
        super().__init__()
        self.dict_ = dict_
        self.default_dict = default_dict
        self.enter_pressed = False
        self.on_dict_update = on_dict_update

        self.update_items()

    def update_items(self):
        self.items.clear()

        keys = list(self.dict_.keys())
        max_width = max([len(x) for x in keys]) + 1
        for key in keys:
            s = "{}: {}".format(key.ljust(max_width), self.dict_[key])
            if self.default_dict is not None:
                if self.dict_[key] != self.default_dict[key]:
                    s += " (modified)"
            self.items.append(s)

    def on_enter_pressed(self):
        self.enter_pressed = True
        self.close()

    def on_char(self, ch):
        if ch == ord("\t"):
            self.edit_dict_value()
            return True
        return False

    def edit_dict_value(self):
        index = self.get_selected_index()
        name = list(self.dict_.keys())[index]
        DictValueEditWindow(
            self.stdscr, self.dict_, name, type(self.dict_[name]),
        ).exec()

        self.on_dict_update(self.dict_)

        self.update_items()
        self.input_.clear()


def init_curses(stdscr):
    curses.noecho()
    curses.cbreak()
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
    stdscr.keypad(1)
    stdscr.nodelay(False)
    stdscr.timeout(1000)


def clear_terminal():
    if sys.platform == "win32":
        os.system("cls")
    else:
        os.system("clear")
