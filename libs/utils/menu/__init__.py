import curses
import curses.ascii
import logging
import os
import re
import sys
import time
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    NamedTuple,
    Optional,
    OrderedDict,
    TypeVar,
    Union,
)

from _shutil import get_hotkey_abbr, slugify

from utils.clip import get_clip, set_clip
from utils.editor import edit_text
from utils.jsonutil import load_json, save_json

GUTTER_SIZE = 1
PROCESS_EVENT_INTERVAL_SEC = 0.1
SHIFT_DOWN = 0x150
SHIFT_UP = 0x151
KEY_A2 = 450
KEY_C2 = 456


def _clamp(n, smallest, largest):
    return max(smallest, min(n, largest))


def _is_backspace_key(ch: Union[int, str]):
    return (
        ch == curses.KEY_BACKSPACE
        or ch == "\b"  # for windows
        or ch == "\x7f"  # for mac and linux
    )


class _Command:
    def __init__(
        self, hotkey: Optional[str], func: Callable, name: Optional[str] = None
    ):
        self.hotkey = hotkey
        self.func = func
        if name is not None:
            self.name = name
        else:
            self.name = func.__name__.strip("_")

    def __str__(self) -> str:
        if self.hotkey is not None:
            return "%s (%s)" % (self.name, get_hotkey_abbr(self.hotkey))
        else:
            return self.name


def _match_fuzzy(item: Any, patt: str) -> bool:
    patt = patt.lower()
    if not patt:
        return True
    else:
        return all([(x in str(item).lower()) for x in patt.split(" ")])


def _match_regex(item: Any, patt: str) -> bool:
    if not patt:
        return True
    else:
        try:
            return re.search(patt, str(item), re.IGNORECASE) is not None
        except re.error:
            return False


def _match(item: Any, patt: str, fuzzy_match: bool, index: int) -> bool:
    if patt[0:1] == ":" and patt[1:].isdigit():
        return int(patt[1:]) == index + 1
    elif fuzzy_match:
        return _match_fuzzy(item, patt)
    else:
        return _match_regex(item, patt)


class _InputWidget:
    def __init__(self, prompt="", text="", ascii_only=False):
        self.prompt = prompt
        self.text = text
        self.set_text(text)
        self.ascii_only = ascii_only

    def set_text(self, text):
        self.text = text
        self.caret_pos = len(text)

    class DrawInputResult(NamedTuple):
        cursor_x: int
        cursor_y: int
        last_x: int
        last_y: int

    def draw_input(self, stdscr, row, show_enter_symbol=False) -> DrawInputResult:
        """_summary_

        Args:
            stdscr (_type_): _description_
            row (_type_): _description_

        Returns:
            int: The index of the last row of text being drawn on the screen.
        """

        assert Menu.stdscr is not None

        # Draw label
        stdscr.addstr(row, 0, self.prompt + ":")

        cursor_y, cursor_x = y, x = Menu.stdscr.getyx()  # type: ignore
        x += 1  # add a space between label and text input

        try:
            stdscr.addstr(y, x, self.text[: self.caret_pos])
            cursor_y, cursor_x = Menu.stdscr.getyx()  # type: ignore

            s = self.text[self.caret_pos :]
            if show_enter_symbol:
                s += " ↵"

            stdscr.addstr(cursor_y, cursor_x, s)
            y, x = Menu.stdscr.getyx()  # type: ignore

        except curses.error:
            pass

        return _InputWidget.DrawInputResult(
            cursor_x=cursor_x, cursor_y=cursor_y, last_x=x, last_y=y
        )

    def clear(self):
        self.text = ""
        self.caret_pos = 0

    def on_char(self, ch):
        if ch == curses.ERR:
            pass
        elif ch == curses.KEY_LEFT or ch == 452:  # curses.KEY_B1
            self.caret_pos = max(self.caret_pos - 1, 0)
        elif ch == curses.KEY_RIGHT or ch == 454:  # curses.KEY_B3
            self.caret_pos = min(self.caret_pos + 1, len(self.text))
        elif _is_backspace_key(ch):
            if self.caret_pos > 0:
                self.text = (
                    self.text[: self.caret_pos - 1] + self.text[self.caret_pos :]
                )
                self.caret_pos = max(self.caret_pos - 1, 0)
        elif ch == curses.ascii.ctrl("u"):
            self.clear()
        # HACK: Workaround for single and double quote on Windows
        elif ch == 530 and sys.platform == "win32":
            self._on_char("'")
        elif ch == 460 and sys.platform == "win32":
            self._on_char('"')
        elif isinstance(ch, str):
            self._on_char(ch)

    def _on_char(self, ch: str):
        if not self.ascii_only or (self.ascii_only and re.match("[\x00-\x7F]", ch)):
            self.text = self.text[: self.caret_pos] + ch + self.text[self.caret_pos :]
            self.caret_pos += 1


T = TypeVar("T")
R = TypeVar("R")


class Menu(Generic[T]):
    stdscr = None
    color_pair_map: Dict[str, int] = {}
    _should_update_screen = False

    def __init__(
        self,
        allow_input=True,
        ascii_only=False,
        cancellable=True,
        close_on_selection=True,
        debug=False,
        history: Optional[str] = None,
        items: Optional[List[T]] = None,
        prompt="",
        text: Optional[str] = None,
        on_item_selected: Optional[Callable[[T], None]] = None,
        highlight: Optional[Union[OrderedDict[str, str], Dict[str, str]]] = None,
        fuzzy_search=True,
        enable_command_palette=True,
        search_on_enter=False,
        selected_index=0,
        wrap_text=False,
        search_mode=True,
        line_number=True,
    ):
        self._is_stdscr_owner: Optional[bool] = None

        self.items: List[T] = items if items is not None else []
        self.last_key_pressed_timestamp: float = 0.0
        self.prev_key: Union[int, str] = -1
        self.is_cancelled: bool = False

        self._allow_input: bool = allow_input
        self._cancellable: bool = cancellable
        self._close_on_selection: bool = close_on_selection
        self._closed: bool = False
        self._debug = debug
        self._height: int = -1
        self._input = _InputWidget(
            prompt=prompt,
            text=text if text else "",
            ascii_only=ascii_only,
        )
        self._last_input: Optional[str] = None
        self.__search_history: List[str] = []
        self._last_item_count = 0
        self._last_selected_item: Optional[T] = None
        self._matched_item_indices: List[int] = []
        self._message: Optional[str] = None
        self._on_item_selected = on_item_selected
        self._highlight = highlight
        self._width: int = -1
        self.__wrap_text: bool = wrap_text
        self.__line_number = line_number

        self.__search_mode = search_mode
        self.__search_on_enter: bool = search_on_enter
        self.__fuzzy_search = fuzzy_search

        self.__scroll_y: int = 0
        self.__num_rendered_items: int = 0
        self.__empty_lines: int = 0

        self.__selected_row_begin: int = selected_index
        self.__selected_row_end: int = selected_index
        self.__multi_select_mode: bool = False

        self.__scroll_x = 0
        self.__can_scroll = False

        self.__should_update_matched_items: bool = False

        # Avoid updating the matching items when input changes too often.
        self.__last_match_time: float = 0

        # Only update screen when _should_update_screen is True. This is set to True to
        # trigger the initial draw.
        self.__should_update_screen = True

        # History
        self.history = history
        if history:
            self.history_values = load_json(self.get_history_file(), [])
            sort_key = {val: i for i, val in enumerate(self.history_values)}
            sorted_items = sorted(
                zip(self.items, list(range(len(self.items)))),
                key=lambda x: sort_key.get(str(x[0]), sys.maxsize),
            )
            self.items = [x[0] for x in sorted_items]
            self.indices = [x[1] for x in sorted_items]

        # Hotkeys
        self._hotkeys: Dict[str, _Command] = {}
        self._custom_commands: List[_Command] = []
        if enable_command_palette:
            self.add_command(self.__command_palette, hotkey="ctrl+p")
            self.add_command(self.select_all, hotkey="ctrl+a")
            self.add_command(self.__toggle_multi_select, hotkey="ctrl+x")
            self.add_command(self.__toggle_wrap, hotkey="alt+z")
            self.add_command(self.__undo, hotkey="alt+u")
            self.add_command(self.paste, hotkey="ctrl+v")
            self.add_command(self.yank, hotkey="ctrl+y")
            self.add_command(self.__edit_text_in_external_editor, hotkey="ctrl+e")

            self._command_palette_menu = Menu(
                prompt="cmd",
                items=self._custom_commands,
                enable_command_palette=False,
            )

            for item in self.items:
                if hasattr(item, "hotkey"):
                    hotkey = item.__dict__["hotkey"]
                    if hotkey:
                        self.add_command(
                            lambda item=item: self.__on_item_hotkey(item),
                            hotkey=hotkey,
                        )

    def __enter__(self):
        if self._is_stdscr_owner is not None:
            raise Exception("Using with-clause on Menu object twice is not allowed")
        self._is_stdscr_owner = Menu.stdscr is None
        if self._is_stdscr_owner:
            Menu.init_curses()

    def __exit__(self, exc_type, exc_val, traceback):
        if self._is_stdscr_owner:
            Menu.destroy_curses()
        else:
            Menu._should_update_screen = True
        self._is_stdscr_owner = None

    def __voice_input(self):
        try:
            from r.speech_to_text import speech_to_text

            text = speech_to_text()
            if text:
                self.set_input(text)
        except Exception as e:
            self.set_message(f"ERROR: {e}")

    def select_all(self):
        self.update_matched_items()

        total_items = len(self.get_item_indices())
        if total_items <= 0:
            return

        self.__multi_select_mode = True
        self.__selected_row_begin = 0
        self.__selected_row_end = total_items - 1

        self.update_screen()

    def __undo(self):
        if len(self.__search_history) > 0:
            last_input = self.__search_history.pop(0)
            self.set_message(last_input)
            self.set_input(last_input, save_search_history=False)

    def yank(self):
        selected_items = self.get_selected_items()
        s = "\n".join([str(x) for x in selected_items])
        set_clip(s)
        self.set_message("copied")

    def paste(self):
        text = get_clip()
        if text != self.get_input():
            self.set_input(text)
            self.update_screen()

    def add_command(
        self, func: Callable, hotkey: Optional[str] = None, name: Optional[str] = None
    ) -> _Command:
        command = _Command(hotkey=hotkey, func=func, name=name)
        self._custom_commands.append(command)

        if hotkey is not None:
            self._hotkeys[hotkey] = command

        return command

    def delete_commands_if(self, condition: Callable[[_Command], bool]):
        for cmd in self._custom_commands[:]:  # Iterate over a copy of the list
            if condition(cmd):
                self._custom_commands.remove(cmd)

    def get_history_file(self):
        from scripting.path import get_data_dir

        return os.path.join(get_data_dir(), "%s_history.json" % slugify(self.history))

    def match_item(self, patt: str, item: T, index: int) -> bool:
        s = str(item)
        return _match(s, patt, fuzzy_match=self.__fuzzy_search, index=index)

    def get_item_indices(self):
        if self.__search_mode:
            return self._matched_item_indices
        else:
            return range(len(self.items))

    def append_item(self, item: T):
        # Clamp selection index to be within a valid range.
        total_items = len(self.get_item_indices())
        self.__selected_row_begin = min(
            max(0, self.__selected_row_begin), total_items - 1
        )
        self.__selected_row_end = min(max(0, self.__selected_row_end), total_items - 1)

        # Check if last line is selected
        last_line_selected = self.__selected_row_end == total_items - 1

        self.items.append(item)
        self._last_item_count = len(self.items)
        added_index = self._last_item_count - 1

        # Scroll to bottom if last line is selected
        if self.__search_mode:
            if self.match_item(self.get_input(), item, added_index):
                self._matched_item_indices.append(added_index)
                if last_line_selected:
                    self.__selected_row_begin = self.__selected_row_end = (
                        len(self._matched_item_indices) - 1
                    )
                self.update_screen()

        if last_line_selected:
            self.__selected_row_begin = self.__selected_row_end = (
                len(self.get_item_indices()) - 1
            )
            self.update_screen()

    def clear_items(self):
        self.items.clear()
        self._last_item_count = 0
        self._matched_item_indices.clear()
        self.__selected_row_begin = 0
        self.__selected_row_end = 0
        self.update_screen()

    def set_input(self, text: str, save_search_history=True):
        self._input.set_text(text)
        if self.__search_mode:
            self.search_by_input(save_search_history=save_search_history)
        self.update_screen()

    def get_input(self) -> str:
        return self._input.text

    def set_prompt(self, prompt: str):
        self._input.prompt = prompt
        self.update_screen()

    def clear_input(self, reset_selection=False):
        if self.__search_mode:
            if reset_selection:
                self.reset_selection()
            elif self.__selected_row_end < len(
                self._matched_item_indices
            ):  # select the same item when filter is removed
                row_number = self._matched_item_indices[self.__selected_row_end]
                self.set_selected_row(row_number)
        self.set_input("")

    def call_func_without_curses(self, func: Callable[[], R]) -> R:
        Menu.destroy_curses()
        ret_val = func()
        Menu.init_curses()
        return ret_val

    def exec(self) -> int:
        with self:
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
        # Enter raw mode. In raw mode, normal line buffering and processing of
        # interrupt, quit, suspend, and flow control keys are turned off. This
        # allows for the use of the hotkey Ctrl-S, which used to be associated
        # with XOFF/XON flow control. Ctrl-S functions as the XOFF command.
        curses.raw()
        curses.cbreak()
        curses.start_color()
        curses.use_default_colors()  # The default color is assigned to -1

        color_pair_index = 1  # note that color pair index starts with 1

        def init_color_pair(name: str, color: int):
            nonlocal color_pair_index

            curses.init_pair(color_pair_index, -1 if name == "white" else color, -1)
            Menu.color_pair_map[name] = color_pair_index
            color_pair_index += 1

            curses.init_pair(color_pair_index, curses.COLOR_BLACK, color)
            Menu.color_pair_map[name.upper()] = color_pair_index
            color_pair_index += 1

        init_color_pair("black", curses.COLOR_BLACK)
        init_color_pair("red", curses.COLOR_RED)
        init_color_pair("green", curses.COLOR_GREEN)
        init_color_pair("yellow", curses.COLOR_YELLOW)
        init_color_pair("blue", curses.COLOR_BLUE)
        init_color_pair("magenta", curses.COLOR_MAGENTA)
        init_color_pair("cyan", curses.COLOR_CYAN)
        init_color_pair("white", curses.COLOR_WHITE)
        init_color_pair("gray", curses.COLOR_WHITE)

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

    def _update_screen(self):
        assert Menu.stdscr is not None

        self._height, self._width = Menu.stdscr.getmaxyx()  # type: ignore

        if sys.platform == "win32":
            Menu.stdscr.clear()
        else:
            # Use erase instead of clear to prevent flickering
            Menu.stdscr.erase()
        self.on_update_screen(item_y_max=self._height - 1)
        Menu.stdscr.refresh()

    def update_matched_items(self, save_search_history=True):
        assert self.__search_mode

        self._matched_item_indices.clear()
        for i, item in enumerate(self.items):
            if self.match_item(self.get_input(), item, i):
                self._matched_item_indices.append(i)

        # Update selected rows
        num_matched_items = len(self._matched_item_indices)
        if num_matched_items > 0:
            self.__selected_row_begin = min(
                self.__selected_row_begin, num_matched_items - 1
            )
            self.__selected_row_end = min(
                self.__selected_row_end, num_matched_items - 1
            )
        else:
            self.__selected_row_begin = 0
            self.__selected_row_end = 0
        self._check_if_item_selection_changed()

        if save_search_history and self._last_input is not None:
            self.__search_history.insert(0, self._last_input)
        self._last_input = self.get_input()
        self._last_item_count = len(self.items)
        self.__last_match_time = time.time()
        self.__should_update_matched_items = False
        self.__should_update_screen = True

    def reset_selection(self):
        self.__selected_row_begin = 0
        self.__selected_row_end = 0

    def set_selected_row(self, selected_row: int):
        self.set_selection(selected_row, selected_row)

    def set_selection(self, begin_row: int, end_row: int):
        self.__selected_row_begin = begin_row
        self.__selected_row_end = end_row

        if self.__search_mode:
            self.update_matched_items()

        total = len(self.get_item_indices())
        if self.__selected_row_begin >= total:
            self.__selected_row_begin = max(0, total - 1)
        if self.__selected_row_end >= total:
            self.__selected_row_end = max(0, total - 1)
        self._check_if_item_selection_changed()

    def refresh(self):
        self.__should_update_matched_items = True

    def __set_selection_by_offset(self, offset: int, multi_select: bool):
        total_rows = len(self.get_item_indices())
        if total_rows > 0:
            selected_row_end = min(
                max(self.__selected_row_end + offset, 0), total_rows - 1
            )
            selected_row_begin = (
                self.__selected_row_begin if multi_select else selected_row_end
            )
            self.set_selection(selected_row_begin, selected_row_end)

    # Returns True if we should exit main loop for the current window
    def process_events(self, timeout_sec: float = 0.0) -> bool:
        assert Menu.stdscr is not None

        if self._closed:
            return True

        if timeout_sec > 0.0:
            Menu.stdscr.timeout(int(timeout_sec * 1000.0))
        else:
            Menu.stdscr.timeout(0)

        if self.__search_mode:
            if (
                self.__should_update_matched_items
                or (
                    time.time() > self.__last_match_time + PROCESS_EVENT_INTERVAL_SEC
                    and (
                        (
                            not self.__search_on_enter
                            and self._last_input != self.get_input()
                        )
                        or self._last_item_count != len(self.items)
                    )
                )
                or (len(self.items) < self._last_item_count)
            ):
                self.update_matched_items()

        # Update screen
        if self.__should_update_screen or Menu._should_update_screen:
            Menu._should_update_screen = False
            self.__should_update_screen = False
            self._update_screen()

        # Keyboard event
        try:
            ch = Menu.stdscr.get_wch()
        except curses.error:
            ch = -1
        except KeyboardInterrupt:
            sys.exit(0)

        if ch != -1:  # getch() will return -1 when timeout
            if self._debug:
                if isinstance(ch, str):
                    self.set_message(f"key={repr(ch)}")
                elif isinstance(ch, int):
                    self.set_message(f"key=0x{ch:x}")

            self.last_key_pressed_timestamp = time.time()
            if self.on_char(ch):
                self.update_screen()

            elif ch == " " and self.get_input() == " ":
                self.set_input("")
                self.call_func_without_curses(lambda: self.__voice_input())

            elif ch == "\n" or ch == "\r":
                self.on_enter_pressed()

            elif ch == curses.KEY_UP or ch == KEY_A2 or ch == SHIFT_UP:
                self.__set_selection_by_offset(
                    offset=-1, multi_select=self.__multi_select_mode or ch == SHIFT_UP
                )

            elif ch == curses.KEY_DOWN or ch == KEY_C2 or ch == SHIFT_DOWN:
                self.__set_selection_by_offset(
                    offset=1, multi_select=self.__multi_select_mode or ch == SHIFT_DOWN
                )

            elif (
                ch == curses.KEY_LEFT or ch == 452  # curses.KEY_B3
            ) and "left" in self._hotkeys:
                self._hotkeys["left"].func()

            elif (
                ch == curses.KEY_LEFT or ch == 452  # curses.KEY_B1
            ) and self.__can_scroll:
                self.__scroll_x = max(self.__scroll_x - self.get_scroll_distance(), 0)
                self.update_screen()

            elif (
                ch == curses.KEY_RIGHT or ch == 454  # curses.KEY_B3
            ) and "right" in self._hotkeys:
                self._hotkeys["right"].func()

            elif (
                ch == curses.KEY_RIGHT or ch == 454  # curses.KEY_B3
            ) and self.__can_scroll:
                self.__scroll_x += self.get_scroll_distance()
                self.update_screen()

            elif ch == curses.KEY_PPAGE or ch == 451:  # curses.KEY_A3
                self.__set_selection_by_offset(
                    offset=-self.get_items_per_page(),
                    multi_select=self.__multi_select_mode,
                )

            elif ch == curses.KEY_NPAGE or ch == 457:  # curses.KEY_C3
                self.__set_selection_by_offset(
                    offset=self.get_items_per_page(),
                    multi_select=self.__multi_select_mode,
                )

            elif ch == curses.KEY_HOME or ch == 449:
                if len(self.get_item_indices()) > 0:
                    begin = (
                        0 if not self.__multi_select_mode else self.__selected_row_begin
                    )
                    end = 0
                    self.set_selection(begin, end)

            elif ch == curses.KEY_END or ch == 455:
                if len(self.get_item_indices()) > 0:
                    end = len(self.get_item_indices()) - 1
                    begin = (
                        end
                        if not self.__multi_select_mode
                        else self.__selected_row_begin
                    )
                    self.set_selection(begin, end)

            elif ch == curses.KEY_DC and "delete" in self._hotkeys:
                self._hotkeys["delete"].func()

            elif self._check_ctrl_hotkey(ch):
                pass

            elif self._check_shift_hotkey(ch):
                pass

            elif self._check_alt_hotkey(ch):
                pass

            elif (
                sys.platform == "win32" and ch == 0x211 and "alt+enter" in self._hotkeys
            ):
                self._hotkeys["alt+enter"].func()

            elif ch == "\x1b":  # escape key
                self.on_escape_pressed()

            elif ch != "\0":
                if self._allow_input:
                    self._input.on_char(ch)
                    self.update_screen()

            self.prev_key = ch

        if ch == -1 and timeout_sec > 0.0:  # getch() is timed-out
            self._on_idle()

        if self._closed:
            self.on_exit()
            return True
        else:
            return False

    def on_escape_pressed(self):
        if "escape" in self._hotkeys:
            logging.debug("Hotkey pressed: escape")
            self._hotkeys["escape"].func()
            return True
        else:
            if self._cancellable:
                self.is_cancelled = True
                self._closed = True
            else:
                self._input.clear()
                self.update_screen()

    def _check_ctrl_hotkey(self, ch: Union[str, int]) -> bool:
        if curses.ascii.isctrl(ch):
            htk = "ctrl+" + curses.ascii.unctrl(ch)[-1].lower()
            if htk in self._hotkeys:
                logging.debug(f"Hotkey pressed: {htk}")
                self._hotkeys[htk].func()
                return True
        return False

    def _check_shift_hotkey(self, ch: Union[str, int]) -> bool:
        if isinstance(ch, str):
            if ch in self._hotkeys:
                self._hotkeys[ch].func()
                return True
            elif len(ch) == 1 and ch.isupper():
                htk = "shift+" + ch.lower()
                if htk in self._hotkeys:
                    logging.debug(f"Hotkey pressed: {htk}")
                    self._hotkeys[htk].func()
                    return True
        return False

    def _check_alt_hotkey(self, ch: Union[int, str]) -> bool:
        is_alt_hotkey = False
        key_name: Optional[str] = None

        if sys.platform == "win32":
            if isinstance(ch, int):
                if ch >= 0x1A1 and ch <= 0x1BA:
                    key_name = chr(ord("a") + (ch - 0x1A1))
                    is_alt_hotkey = True
        else:
            if ch == "\x1b":
                assert Menu.stdscr is not None
                # Try to immediately get the next key after ALT
                Menu.stdscr.nodelay(True)
                ch2 = Menu.stdscr.getch()
                Menu.stdscr.nodelay(False)
                if isinstance(ch2, int) and (
                    (ch2 >= ord("a") and ch2 <= ord("z"))
                    or ch2 == ord("\r")
                    or ch2 == ord("\n")
                ):
                    key_name = chr(ch2)
                    is_alt_hotkey = True

        if key_name == "\n" or key_name == "\r":
            key_name = "enter"

        if key_name is not None:
            htk = "alt+" + key_name
            if htk in self._hotkeys:
                logging.debug(f"Hotkey pressed: {htk}")
                self._hotkeys[htk].func()
            elif key_name == "enter":  # alt + enter
                self._input.on_char("\n")  # new line
                self.update_screen()

        return is_alt_hotkey

    def _on_idle(self):
        self.on_idle()

    def on_exit(self):
        pass

    def on_idle(self):
        pass

    def _reset_state(self):
        self.is_cancelled = False
        self._closed = False

    def _exec(self):
        self._reset_state()
        self.update_screen()
        self.on_created()
        self.on_main_loop()
        while not self.process_events(timeout_sec=PROCESS_EVENT_INTERVAL_SEC):
            self.on_main_loop()

    def get_selected_index(self):
        if self.is_cancelled:
            return -1
        elif len(self.get_item_indices()) > 0:
            return self.get_item_indices()[self.__selected_row_end]
        else:
            return -1

    def get_text(self) -> Optional[str]:
        if self.is_cancelled:
            return None
        else:
            return self._input.text

    def get_items_per_page(self):
        return self.__num_rendered_items + self.__empty_lines

    class DrawTextResult(NamedTuple):
        last_y: int
        can_scroll_left: bool
        can_scroll_right: bool

    def color_name_to_attr(self, color: str) -> int:
        attr = curses.color_pair(Menu.color_pair_map[color])
        if color == "gray":
            attr |= curses.A_DIM
        return attr

    def draw_text(
        self,
        row: int,
        col: int,
        s: str,
        color: str = "white",
        wrap_text=False,
        scroll_x=0,
        bold=False,
    ) -> DrawTextResult:
        """_summary_

        Args:
            row (int): _description_
            col (int): _description_
            s (str): _description_

        Returns:
            int: The index of the last row of text being drawn on the screen.
        """
        assert Menu.stdscr is not None
        assert row >= 0
        assert col >= 0

        if row >= self._height:
            raise Exception(
                "Row number should be smaller than the height of the screen."
            )

        s = s[scroll_x:]

        # Draw left arrow
        if scroll_x > 0:
            Menu.stdscr.addstr(row, col, "<", self.color_name_to_attr("CYAN"))
            x = col + 1
        else:
            x = col

        last_row_index = y = row
        can_scroll_right = False
        attr = self.color_name_to_attr(color)
        if bold:
            attr |= curses.A_BOLD
        for i, ch in enumerate(s):
            try:
                Menu.stdscr.addstr(y, x, ch, attr)
            except curses.error:
                # Tolerate "addwstr() returned ERR" when drawing the character at the bottom right corner.
                pass
            except ValueError:
                # If an invalid character is passed, simply stop rendering, for example, an "embedded null character".
                break

            last_y = y

            # Get current cursor position
            y, x = Menu.stdscr.getyx()  # type: ignore
            if wrap_text:
                if y >= self._height:
                    last_row_index = self._height - 1
                    break
                elif y > last_y:
                    x = col
            else:
                if y > last_y:
                    if i < len(s) - 1:
                        last_row_index = row
                        Menu.stdscr.addstr(
                            row,
                            self._width - 1,
                            ">",
                            self.color_name_to_attr("CYAN"),
                        )
                        can_scroll_right = True
                    break
            if x > col:
                last_row_index = y

        return Menu.DrawTextResult(
            last_y=last_row_index,
            can_scroll_left=scroll_x > 0,
            can_scroll_right=can_scroll_right,
        )

    def get_item_text(self, item: T) -> str:
        return str(item)

    def goto_line(self, line: int):
        self.__scroll_y = line

    def on_update_screen(self, item_y_max: int):
        assert Menu.stdscr is not None

        # Render input widget
        draw_input_result = self._input.draw_input(
            Menu.stdscr,
            0,
            show_enter_symbol=self.__should_trigger_search(),
        )

        # Get matched scripts
        item_y = draw_input_result.last_y + 2

        item_indices = self.get_item_indices()

        # Update scroll y.
        items_per_page = self.get_items_per_page()
        if items_per_page > 0:
            if self.__selected_row_end >= self.__scroll_y + items_per_page:
                self.__scroll_y = _clamp(
                    self.__selected_row_end,
                    0,
                    len(item_indices) - items_per_page + 1,
                )
            elif self.__selected_row_end < self.__scroll_y:
                self.__scroll_y = _clamp(
                    self.__selected_row_end,
                    0,
                    len(item_indices) - items_per_page + 1,
                )

        self.__can_scroll = False
        matched_item_index = self.__scroll_y

        if self.__line_number and len(item_indices) > 0:
            line_number_width = len(str(item_indices[-1] + 1))
        else:
            line_number_width = 0

        assert len(item_indices) <= len(self.items)
        while matched_item_index < len(item_indices) and item_y < item_y_max:
            item_index = item_indices[matched_item_index]
            self.__num_rendered_items = matched_item_index - self.__scroll_y + 1
            is_item_selected = (
                matched_item_index >= self.__selected_row_begin
                and matched_item_index <= self.__selected_row_end
            ) or (
                matched_item_index <= self.__selected_row_begin
                and matched_item_index >= self.__selected_row_end
            )
            item = self.items[item_index]
            item_text = self.get_item_text(self.items[item_index])

            if hasattr(item, "color"):
                color = item.__dict__["color"]
            else:
                # Highlight text by regex
                color = "white"
                if self._highlight is not None:
                    for patt, c in self._highlight.items():
                        if re.search(patt, item_text):
                            color = c

            # Draw item
            draw_text_result = self.draw_text(
                item_y,
                line_number_width + GUTTER_SIZE,
                item_text,
                wrap_text=self.__wrap_text,
                color=color.upper() if is_item_selected else color,
                scroll_x=self.__scroll_x,
            )

            # Draw line number
            if self.__line_number:
                line_number = f"{item_index + 1}"
                line_number_text = f"{line_number}"
                line_number_color = "WHITE" if is_item_selected else "gray"
                self.draw_text(
                    item_y,
                    0,
                    line_number_text.rjust(line_number_width) + (" " * GUTTER_SIZE),
                    color=line_number_color,
                )

                for y in range(item_y + 1, draw_text_result.last_y + 1):
                    self.draw_text(
                        y,
                        0,
                        " " * (line_number_width + GUTTER_SIZE),
                        color=line_number_color,
                    )

            increments = draw_text_result.last_y + 1 - item_y
            if self.__wrap_text:
                matched_item_index += 1
            else:
                matched_item_index += increments
            item_y += increments
            self.__empty_lines = max(0, item_y_max - draw_text_result.last_y - 1)

            if draw_text_result.can_scroll_left or draw_text_result.can_scroll_right:
                self.__can_scroll = True

        if items_per_page != self.get_items_per_page():
            self.__should_update_screen = True

        # Draw status bar
        a = self.get_status_bar_text()
        b = " [%d/%d]" % (
            self.__selected_row_end + 1,
            len(item_indices),
        )
        self.draw_text(
            row=self._height - 1,
            col=0,
            s=f"{a[:self._width - len(b)]:<{self._width - len(b)}}{b:>{len(b)}}",
            color="WHITE",
        )

        # Move cursor
        try:
            Menu.stdscr.move(draw_input_result.cursor_y, draw_input_result.cursor_x)
        except curses.error:
            pass

    def get_scroll_distance(self) -> int:
        return 10

    def get_status_bar_text(self) -> str:
        columns: List[str] = []
        if self.__multi_select_mode:
            columns.append("multi_select_mode")
        if self._message:
            columns.append(self._message)
        return " | ".join(columns)

    def get_selected_item(self, ignore_cancellation=False) -> Optional[T]:
        if not ignore_cancellation and self.is_cancelled:
            return None
        elif len(self.get_item_indices()) > 0:
            item_index = self.get_item_indices()[self.__selected_row_end]
            return self.items[item_index]
        else:
            return None

    def get_selected_indices(self) -> Iterator[int]:
        if len(self.get_item_indices()) > 0:
            i = self.__selected_row_begin
            j = self.__selected_row_end
            if i > j:
                i, j = j, i
            for idx in self.get_item_indices()[i : j + 1]:
                yield idx
        else:
            return

    def get_selected_items(self) -> Iterator[T]:
        for item_index in self.get_selected_indices():
            yield self.items[item_index]

    def on_char(self, ch: int):
        if ch == "\t":
            item = self.get_selected_item()
            if item is not None:
                self.set_input("%s" % item)
            return True

        elif ch == curses.ascii.ctrl("c"):
            sys.exit(0)

        elif ch in self._hotkeys:
            self._hotkeys[ch].func()
            return True

        else:
            return False

    def __should_trigger_search(self) -> bool:
        if self.__search_mode:
            return self.__search_on_enter and self.get_input() != self._last_input
        else:
            return False

    def search_by_input(self, save_search_history=True) -> bool:
        if self.__should_trigger_search():
            self.update_matched_items(save_search_history=save_search_history)
            return True
        else:
            return False

    def on_enter_pressed(self):
        if self.search_by_input():
            return

        else:
            item = self.get_selected_item()
            if item is not None:
                on_item_selected = self._on_item_selected
                if on_item_selected is not None:
                    self.call_func_without_curses(
                        lambda item=item: on_item_selected(item)
                    )
            if self._close_on_selection:
                self.close()
            else:
                self.update_screen()

    def on_tab_pressed(self):
        pass

    def on_main_loop(self):
        pass

    def on_created(self):
        pass

    def close(self):
        self._closed = True

    def cancel(self):
        self.is_cancelled = True
        self._closed = True

    def _check_if_item_selection_changed(self):
        selected = None
        item_indices = self.get_item_indices()
        item_index = -1
        if self.__selected_row_end < len(item_indices):
            item_index = item_indices[self.__selected_row_end]
            if item_index < len(self.items):
                selected = self.items[item_index]

        if selected != self._last_selected_item or self._last_input != self.get_input():
            self.on_item_selection_changed(selected, i=item_index)
            self.update_screen()
        self._last_selected_item = selected

    def on_item_selection_changed(self, item: Optional[T], i: int):
        pass

    def set_message(self, message: Optional[str] = None):
        self._message = message
        self.update_screen()

    def __edit_text_in_external_editor(self):
        text = self.get_input()
        text = self.call_func_without_curses(lambda: edit_text(text))
        self.set_input(text)

    def __command_palette(self):
        self._command_palette_menu.exec()
        hotkey = self._command_palette_menu.get_selected_item()
        if hotkey is not None:
            hotkey.func()
        self.update_screen()

    def update_screen(self):
        self.__should_update_screen = True

    def __toggle_multi_select(self):
        self.set_multi_select(not self.__multi_select_mode)

    def __toggle_wrap(self):
        self.__wrap_text = not self.__wrap_text
        self.update_screen()

    def set_multi_select(self, mode: bool):
        self.__multi_select_mode = mode
        if not self.__multi_select_mode:
            self.__selected_row_begin = self.__selected_row_end
        self.update_screen()

    def __on_item_hotkey(self, item: T):
        # Select the item.
        self.__selected_row_begin = self.__selected_row_end = self.items.index(item)
        if self._close_on_selection:
            self.close()
        else:
            self.update_screen()
