import ctypes
import curses
import curses.ascii
import locale
import os
import re
import sys
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar

from _shutil import load_json, save_json, slugify


def activate_cur_terminal():
    if sys.platform == "win32":
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        ctypes.windll.user32.SetForegroundWindow(hwnd)


def minimize_cur_terminal():
    if sys.platform == "win32":
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        ctypes.windll.user32.ShowWindow(hwnd, 6)


def _select_options_ncurse(options, history=""):
    if not options:
        raise Exception("Options cannot be empty.")
    return Menu(items=options, history=history).exec()


def select_option(options, history=""):
    return _select_options_ncurse(options, history=history)


def _prompt(options, message=None):
    for i, option in enumerate(options):
        print("%d. %s" % (i + 1, option))

    if message is None:
        message = "selections"

    print("%s (indices, sep by space)> " % message, flush=True, end="")
    input_ = input()
    selections = [int(x) - 1 for x in input_.split()]
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
    kw = kw.lower()
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


T = TypeVar("T")


class MenuItem:
    def __init__(
        self, name: str, callback: Optional[Callable[[], None]] = None
    ) -> None:
        self.name = name
        self.callback = callback

    def __str__(self):
        return self.name


def ceildiv(a, b):
    return -(a // -b)


def get_hotkey_abbr(hotkey):
    return (
        hotkey.lower()
        .replace("win+", "#")
        .replace("ctrl+", "^")
        .replace("alt+", "!")
        .replace("shift+", "+")
    )


def to_ascii_hotkey(hotkey: str) -> int:
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


class InternalHotkey:
    def __init__(self, hotkey: str, func: Callable):
        self.hotkey = hotkey
        self.func = func

    def __str__(self) -> str:
        return "%s (%s)" % (self.func.__name__, get_hotkey_abbr(self.hotkey))


class Menu:
    stdscr = None

    def __init__(
        self,
        items: List = [],
        label="",
        text="",
        ascii_only=False,
        cancellable=True,
        close_on_selection=False,
        history: Optional[str] = None,
    ):
        self._input = InputWidget(label=label + ">", text=text, ascii_only=ascii_only)
        self.items = items
        self.closed = False
        self.matched_item_indices: List[int] = []
        self.selected_row = 0
        self.width = -1
        self.height = -1
        self.message = None
        self.cancellable = cancellable
        self.last_key_pressed_timestamp = 0.0
        self.last_input = None
        self.last_item_count = 0
        self.prev_key = -1
        self.close_on_selection = close_on_selection
        self.should_refresh = False

        # Only update screen when invalidated is True. This is set to True to
        # trigger the initial draw.
        self.invalidated = True

        # History
        self.history = history
        if history:
            self.history_values = load_json(self.get_history_file(), [])
            sort_key = {val: i for i, val in enumerate(self.history_values)}
            sorted_items = sorted(
                zip(self.items, list(range(len(self.items)))),
                key=lambda x: sort_key.get(str(x[0]), sys.maxsize),
            )
            self.items, self.indices = zip(*sorted_items)

        # Hotkeys
        self.internal_hotkeys: Dict[int, InternalHotkey] = {}

    def add_hotkey(self, hotkey, func):
        ch = to_ascii_hotkey(hotkey)
        self.internal_hotkeys[ch] = InternalHotkey(hotkey=hotkey, func=func)

    def get_history_file(self):
        from _script import get_data_dir

        return os.path.join(get_data_dir(), "%s_history.json" % slugify(self.history))

    def item(self, name=None):
        def decorator(func):
            nonlocal name
            if name is None:
                name = func.__name__
            self.items.append(MenuItem(name=name, callback=func))
            return func

        return decorator

    def set_input(self, text: str):
        self._input.set_text(text)

    def get_input(self) -> str:
        return self._input.text

    def set_prompt(self, prompt: str):
        self._input.label = prompt

    def clear_input(self):
        self._input.clear()
        self.reset_selection()
        self.invalidated = True

    def run_cmd(self, func):
        Menu.destroy_curses()
        func()
        Menu.init_curses()

    def exec(self) -> int:
        if Menu.stdscr is None:
            try:
                Menu.init_curses()
                self._exec()
            finally:
                Menu.destroy_curses()
        else:
            self._exec()

        idx = self.get_selected_index()
        if self.history is not None and idx >= 0:
            try:
                self.history_values.remove(str(self.items[idx]))
            except ValueError:
                pass
            self.history_values.insert(0, str(self.items[idx]))
            save_json(self.get_history_file(), self.history_values)
            idx = self.indices[idx]

        return idx

    @staticmethod
    def init_curses():
        if Menu.stdscr is not None:
            return

        # Remove escape key delay for Linux system
        # See also: ESCDELAY in https://linux.die.net/man/3/ncurses
        os.environ.setdefault("ESCDELAY", "25")

        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.start_color()
        curses.use_default_colors()  # The default color is assigned to the color number -1
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
        stdscr.keypad(True)
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
        assert Menu.stdscr is not None

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
        self.reset_selection()

    def reset_selection(self):
        self.selected_row = 0

    def refresh(self):
        self.should_refresh = True

    # Returns false if we should exit main loop for the current window
    def process_events(self, blocking=True) -> bool:
        assert Menu.stdscr is not None

        if blocking:
            Menu.stdscr.timeout(1000)
        else:
            Menu.stdscr.timeout(0)

        self.should_refresh = (
            self.should_refresh
            or self.last_input != self.get_text()
            or self.last_item_count != len(self.items)
        )
        if not blocking or self.should_refresh:
            self.last_input = self.get_text()
            self.last_item_count = len(self.items)
            self.update_matched_items()
            self.should_refresh = False

        if self.invalidated:
            self.update_screen()
            self.invalidated = False

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
                self.invalidated = True

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
                self._input.clear()
                self.invalidated = True
                if self.cancellable:
                    self.matched_item_indices.clear()
                    return False

            elif ch != 0:
                self._input.on_char(ch)
                self.invalidated = True

            self.prev_key = ch

        if ch == -1 and blocking:  # getch() is timed-out
            self.on_idle()

        if self.closed:
            return False

        return True

    def on_idle(self):
        pass

    def _exec(self):
        self.on_main_loop()
        while self.process_events():
            self.on_main_loop()

    def get_selected_index(self):
        if len(self.matched_item_indices) > 0:
            return self.matched_item_indices[self.selected_row]
        else:
            return -1

    def get_text(self):
        return self._input.text

    def get_items_per_page(self):
        return self.height - 2

    def draw_text(self, row, col, s, highlight_parenthesis=False):
        assert Menu.stdscr is not None

        TAB_SIZE = 8
        if row >= self.height:
            return

        if col < 0:
            s = ".." + s[-col + 2 :]
            col = 0

        j = col
        for ch in s:
            if highlight_parenthesis and ch == "(":
                Menu.stdscr.attron(curses.color_pair(1))

            if ch == "\t":
                next_j = (j // TAB_SIZE + 1) * TAB_SIZE
                ch = " " * (next_j - j)
            else:
                next_j = j + 1

            try:
                Menu.stdscr.addstr(row, j, ch)
            except curses.error:
                # Tolerate "addwstr() returned ERR"
                pass

            if highlight_parenthesis and ch == ")":
                Menu.stdscr.attroff(curses.color_pair(1))

            j = next_j

        Menu.stdscr.attroff(curses.color_pair(1))

    def on_update_screen(self, max_height=-1):
        assert Menu.stdscr is not None

        if max_height < 0:
            max_height = self.height

        # Get matched scripts
        row = 2
        items_per_page = self.get_items_per_page()

        current_page_index = self.selected_row // items_per_page
        selected_index_in_page = self.selected_row % items_per_page
        indices_in_page = self.matched_item_indices[
            current_page_index * items_per_page :
        ]
        for i, item_index in enumerate(indices_in_page):
            # Index
            if i == selected_index_in_page:  # hightlight on
                Menu.stdscr.attron(curses.color_pair(2))
            s = "{:>4}".format(item_index + 1)
            self.draw_text(row, 0, s, highlight_parenthesis=True)
            if i == selected_index_in_page:  # highlight off
                Menu.stdscr.attroff(curses.color_pair(2))

            # Item name
            self.draw_text(
                row, 5, str(self.items[item_index]), highlight_parenthesis=True
            )

            row += 1
            if row >= max_height:
                break

        matched_item_str = "(%d/%d)" % (
            self.selected_row + 1,
            len(self.matched_item_indices),
        )
        self.draw_text(0, self.width - len(matched_item_str), matched_item_str)

        if self.message is not None:
            Menu.stdscr.attron(curses.color_pair(3))
            Menu.stdscr.addstr(1, 0, self.message)
            Menu.stdscr.attroff(curses.color_pair(3))

        # Render input widget at the end, so the cursor will be move to the correct position
        self._input.on_update_screen(Menu.stdscr, 0, cursor=True)

    def get_selected_item(self):
        if len(self.matched_item_indices) > 0:
            item_index = self.matched_item_indices[self.selected_row]
            return self.items[item_index]
        else:
            return None

    def on_char(self, ch):
        if ch == ord("\t"):
            item = self.get_selected_item()
            if item is not None:
                self.set_input("%s" % item)
            return True

        elif ch == curses.ascii.ctrl(ord("c")):
            sys.exit(0)

        elif ch in self.internal_hotkeys:
            self.internal_hotkeys[ch].func()
            return True

        else:
            return False

    def on_enter_pressed(self):
        item = self.get_selected_item()
        if item is not None and hasattr(item, "callback") and callable(item.callback):
            self.run_cmd(lambda item=item: item.callback())
            if self.close_on_selection:
                self.close()
        else:
            self.close()
        self.invalidated = True

    def on_tab_pressed(self):
        pass

    def on_main_loop(self):
        pass

    def close(self):
        self.closed = True

    def on_item_selected(self):
        self.invalidated = True

    def set_message(self, message=None):
        self.message = message
        self.invalidated = True


class DictValueEditWindow(Menu):
    def __init__(
        self,
        dict_,
        name,
        type,
        dict_history_values: List,
        items: List,
    ):
        self.dict_ = dict_
        self.dict_history_values = dict_history_values
        self.name = name
        self.type = type

        super().__init__(
            items=items,
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
        elif self.type == bool or self.type == type(None):
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

        # Save edit history
        if val in self.dict_history_values:  # avoid duplicates
            self.dict_history_values.remove(val)
        self.dict_history_values.insert(0, val)

        self.close()

    def on_char(self, ch):
        if ch == ord("\t"):
            val = self.get_selected_item()
            if val is not None:
                self.set_input(val)
            return True
        elif ch == curses.KEY_DC:  # delete key
            i = self.get_selected_index()
            del self.dict_history_values[i]
            return True

        return False


class DictEditWindow(Menu):
    def __init__(
        self,
        dict_,
        default_dict=None,
        on_dict_update: Optional[Callable[[Dict], None]] = None,
        dict_history: Dict[str, List[Any]] = {},
        on_dict_history_update: Optional[Callable[[Dict[str, List[Any]]], None]] = None,
        label="",
    ):
        super().__init__(label=label)
        self.dict_ = dict_
        self.default_dict = default_dict
        self.enter_pressed = False
        self.on_dict_update = on_dict_update
        self.label = label
        self.dict_history = dict_history
        self.on_dict_history_update = on_dict_history_update

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

        if name not in self.dict_history:
            dict_history_values = self.dict_history[name] = []
        else:
            dict_history_values = self.dict_history[name]

        DictValueEditWindow(
            dict_=self.dict_,
            name=name,
            type=type(val),
            items=dict_history_values,
            dict_history_values=dict_history_values,
        ).exec()

        if self.on_dict_update:
            self.on_dict_update(self.dict_)
        if self.on_dict_history_update:
            self.on_dict_history_update(self.dict_history)

        self.update_items()
        self._input.clear()


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
