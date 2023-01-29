import ctypes
import curses
import curses.ascii
import locale
import logging
import os
import re
import sys
import time

from _script import get_data_dir
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


def _select_options_ncurse(options, save_history=""):
    assert isinstance(save_history, str)

    def get_history_file():
        return os.path.join(get_data_dir(), "%s.json" % save_history)

    if save_history:
        os.makedirs("tmp", exist_ok=True)
        history = load_json(get_history_file(), [])
        sort_key = {x: i for i, x in enumerate(history)}
        options, indices = zip(
            *sorted(
                zip(options, list(range(len(options)))),
                key=lambda x: sort_key[x[0]] if x[0] in sort_key else sys.maxsize,
            )
        )

    w = Menu(items=options)
    idx = w.exec()

    if save_history and idx >= 0:
        try:
            history.remove(options[idx])
        except ValueError:
            pass
        history.insert(0, options[idx])
        save_json(get_history_file(), history)
        idx = indices[idx]

    return idx


def select_option(options, save_history=""):
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


def _is_backspace_key(ch):
    return ch in (
        curses.KEY_BACKSPACE,
        ord("\b"),  # for windows
        0x7F,  # for mac
    )


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
        elif _is_backspace_key(ch):
            if self.caret_pos > 0:
                self.text = (
                    self.text[: self.caret_pos - 1] + self.text[self.caret_pos :]
                )
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
    stdscr = None

    def __init__(
        self,
        items=[],
        label="",
        text="",
        ascii_only=False,
        cancellable=True,
    ):
        self.input_ = InputWidget(label=label + ">", text=text, ascii_only=ascii_only)
        self.items = items
        self.on_items = []
        self.closed = False
        self.matched_item_indices = []
        self.selected_row = 0
        self.width = -1
        self.height = -1
        self.message = None
        self.cancellable = cancellable
        self.last_key_pressed_timestamp = 0
        self.last_input = None
        self.last_item_count = 0

    def item(self, name=None):
        def decorator(func):
            nonlocal name
            if name is None:
                name = func.__name__

            self.items.append(name)
            self.on_items.append(func)

            return func

        return decorator

    def run_cmd(self, func):
        Menu.destroy_curses()
        func()
        Menu.init_curses()

    def exec(self) -> int:
        if Menu.stdscr is None:
            try:
                Menu.init_curses()
                self.exec_()
            finally:
                Menu.destroy_curses()
        else:
            self.exec_()

        return self.get_selected_index()

    @staticmethod
    def init_curses():
        if Menu.stdscr is not None:
            return
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
        stdscr.keypad(1)
        stdscr.nodelay(False)
        stdscr.timeout(1000)
        Menu.stdscr = stdscr

    @staticmethod
    def destroy_curses():
        if Menu.stdscr is None:
            return
        curses.endwin()
        Menu.stdscr = None

    def update_screen(self):
        self.height, self.width = Menu.stdscr.getmaxyx()

        if sys.platform == "win32":
            Menu.stdscr.clear()
        else:
            # Use erase instead of clear to prevent flickering
            Menu.stdscr.erase()
        self.on_update_screen()
        Menu.stdscr.refresh()

    def update_matched_items(self):
        # Search scripts
        self.matched_item_indices = list(
            _fuzzy_search_func(self.items, self.get_text())
        )

        self.selected_row = 0

    def process_events(self, blocking=True):
        if blocking:
            Menu.stdscr.timeout(1000)
        else:
            Menu.stdscr.timeout(0)

        if not blocking or (
            self.last_input != self.get_text()
            or self.last_item_count != len(self.items)
        ):
            self.last_input = self.get_text()
            self.last_item_count = len(self.items)
            self.update_matched_items()

        self.update_screen()

        # Keyboard event
        try:
            ch = Menu.stdscr.getch()
        except KeyboardInterrupt:
            sys.exit(0)

        # Workaround for arrow keys in Alacritty
        ALACRITTY_UP = 450
        ALACRITTY_DOWN = 456

        if ch != -1:  # getch() will return -1 when timeout
            self.last_key_pressed_timestamp = time.time()
            if self.on_char(ch):
                pass

            elif ch == ord("\n"):
                self.on_enter_pressed()

            elif ch == curses.KEY_UP or ch == ALACRITTY_UP:
                self.selected_row = max(self.selected_row - 1, 0)
                self.on_item_selected()

            elif ch == curses.KEY_DOWN or ch == ALACRITTY_DOWN:
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
                    return True

            elif ch != 0:
                self.input_.on_char(ch)

        if self.closed:
            return True

        return False

    def exec_(self):
        self.on_main_loop()
        while True:
            if self.process_events():
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

    def print_str(self, row, col, s):
        if row >= self.height:
            return

        for i, ch in enumerate(s):
            if ch == "(":
                Menu.stdscr.attron(curses.color_pair(1))

            try:
                Menu.stdscr.addstr(row, col + i, ch)
            except curses.error:
                # Tolerate "addwstr() returned ERR"
                pass

            if ch == ")":
                Menu.stdscr.attroff(curses.color_pair(1))

        Menu.stdscr.attroff(curses.color_pair(1))

    def on_update_screen(self, max_height=-1):
        if max_height < 0:
            max_height = self.height

        # Get matched scripts
        row = 2
        items_per_page = self.get_items_per_page()

        page = self.selected_row // items_per_page
        selected_index_in_page = self.selected_row % items_per_page
        indices_in_page = self.matched_item_indices[page * items_per_page :]
        for i, item_index in enumerate(indices_in_page):
            if i == selected_index_in_page:  # hightlight on
                Menu.stdscr.attron(curses.color_pair(2))
            s = "{:>2}  {}".format(item_index + 1, self.items[item_index])
            self.print_str(row, 0, s)
            if i == selected_index_in_page:  # highlight off
                Menu.stdscr.attroff(curses.color_pair(2))

            row += 1
            if row >= max_height:
                break

        self.input_.on_update_screen(Menu.stdscr, 0, cursor=True)

        if self.message is not None:
            Menu.stdscr.attron(curses.color_pair(3))
            Menu.stdscr.addstr(1, 0, self.message)
            Menu.stdscr.attroff(curses.color_pair(3))

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

    def set_message(self, message):
        self.message = message
        self.update_screen()


class DictValueEditWindow(Menu):
    def __init__(self, dict_, name, type, default_vals=[]):
        self.dict_ = dict_
        self.name = name
        self.type = type

        super().__init__(
            items=default_vals,
            label=name,
            text="",
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
    def __init__(self, dict_, default_dict=None, on_dict_update=None, label=""):
        super().__init__(label=label)
        self.dict_ = dict_
        self.default_dict = default_dict
        self.enter_pressed = False
        self.on_dict_update = on_dict_update
        self.label = label

        self.update_items()

    def update_items(self):
        self.items.clear()

        keys = list(self.dict_.keys())
        max_width = max([len(x) for x in keys]) + 1
        for key in keys:
            s = "{}: {}".format(key.ljust(max_width), self.dict_[key])
            if self.default_dict is not None:
                if self.dict_[key] != self.default_dict[key]:
                    s += " (*)"
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
        val = self.dict_[name]
        DictValueEditWindow(
            self.dict_,
            name,
            type(val),
            default_vals=[val],
        ).exec()

        self.on_dict_update(self.dict_)

        self.update_items()
        self.input_.clear()


def clear_terminal():
    if sys.platform == "win32":
        os.system("cls")
    else:
        os.system("clear")


def get_terminal_title():
    if sys.platform == "win32":
        MAX_BUFFER = 260
        title_buff = (ctypes.c_char * MAX_BUFFER)()
        ret = ctypes.windll.kernel32.GetConsoleTitleA(title_buff, MAX_BUFFER)
        assert ret > 0
        return title_buff.value.decode(locale.getpreferredencoding())


def set_terminal_title(title):
    if sys.platform == "win32":
        win_title = title.encode(locale.getpreferredencoding())
        ctypes.windll.kernel32.SetConsoleTitleA(win_title)
