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

from _shutil import get_hotkey_abbr, load_json, save_json, slugify

from utils.clip import get_clip, set_clip


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


def _match(item: Any, patt: str, fuzzy_match: bool) -> bool:
    if fuzzy_match:
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
        stdscr.addstr(row, 0, self.prompt)

        y, x = Menu.stdscr.getyx()  # type: ignore
        x += 1  # add a space between label and text input

        try:
            stdscr.addstr(y, x, self.text[: self.caret_pos])
            cursor_y, cursor_x = Menu.stdscr.getyx()  # type: ignore
            stdscr.addstr(
                cursor_y,
                cursor_x,
                self.text[self.caret_pos :] + (" \u23CE" if show_enter_symbol else ""),
            )
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
        elif ch == curses.ascii.ctrl("a"):
            self.clear()
        elif ch == "\n":
            pass

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


class Menu(Generic[T]):
    stdscr = None
    color_pair_map: Dict[str, int] = {}

    def __init__(
        self,
        allow_input=True,
        ascii_only=False,
        cancellable=True,
        close_on_selection=True,
        debug=False,
        history: Optional[str] = None,
        items: List[T] = [],
        prompt="",
        text="",
        on_item_selected: Optional[Callable[[T], None]] = None,
        highlight: Optional[OrderedDict[str, str]] = None,
        fuzzy_search=True,
        enable_command_palette=True,
        wrap_text=False,
        search_on_enter=False,
    ):
        self.items = items
        self.last_key_pressed_timestamp: float = 0.0
        self.prev_key: Union[int, str] = -1
        self.is_cancelled: bool = False

        self._allow_input: bool = allow_input
        self._cancellable: bool = cancellable
        self._close_on_selection: bool = close_on_selection
        self._closed: bool = False
        self._debug = debug
        self._fuzzy_search = fuzzy_search
        self._height: int = -1
        self._input = _InputWidget(prompt=prompt, text=text, ascii_only=ascii_only)
        self._last_input: Optional[str] = None
        self._last_item_count = 0
        self._last_selected_item: Optional[T] = None
        self._matched_item_indices: List[int] = []
        self._message: Optional[str] = None
        self._on_item_selected = on_item_selected
        self._requested_selected_row: int = -1
        self._highlight = highlight
        self._width: int = -1
        self._wrap_text: bool = wrap_text
        self.__search_on_enter: bool = search_on_enter

        self._selected_row_begin: int = 0
        self._selected_row_end: int = 0
        self._multi_select_mode: bool = False

        self._scroll_x = 0
        self._scroll_distance = 0
        self._can_scroll_left = False
        self._can_scroll_right = False

        self._should_update_matched_items: bool = False

        # Avoid updating the matching items when input changes too often.
        self._last_match_time: float = 0

        # Only update screen when _should_update_screen is True. This is set to True to
        # trigger the initial draw.
        self._should_update_screen = True

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
            self.add_command(self._toggle_multi_select, hotkey="ctrl+x")
            self.add_command(self._palette, hotkey="ctrl+p")
            self.add_command(self._paste, hotkey="ctrl+v")
            self.add_command(self._yank, hotkey="ctrl+y")

            self._command_palette_menu = Menu(
                prompt="command palette:",
                items=self._custom_commands,
                enable_command_palette=False,
            )

    def _yank(self):
        selected_items = self.get_selected_items()
        s = "\n".join([str(x) for x in selected_items])
        set_clip(s)
        self.set_message("copied")

    def _paste(self):
        self.set_input(get_clip())

    def add_command(
        self, func: Callable, hotkey: Optional[str] = None, name: Optional[str] = None
    ) -> _Command:
        command = _Command(hotkey=hotkey, func=func, name=name)
        self._custom_commands.append(command)

        if hotkey is not None:
            self._hotkeys[hotkey] = command

        return command

    def get_history_file(self):
        from _script import get_data_dir

        return os.path.join(get_data_dir(), "%s_history.json" % slugify(self.history))

    def match_item(self, patt: str, item: T) -> bool:
        s = str(item)
        return _match(s, patt, fuzzy_match=self._fuzzy_search)

    def append_item(self, item: T):
        last_line_selected = (
            self._selected_row_end == len(self._matched_item_indices) - 1
        )

        self.items.append(item)
        self._last_item_count = len(self.items)
        if self.match_item(self.get_input(), item):
            self._matched_item_indices.append(self._last_item_count - 1)

            # Scroll to bottom if last line is selected
            if last_line_selected:
                self._selected_row_begin = self._selected_row_end = (
                    len(self._matched_item_indices) - 1
                )

            self.update_screen()

    def clear_items(self):
        self.items.clear()
        self._last_item_count = 0
        self._matched_item_indices.clear()
        self._selected_row_begin = 0
        self._selected_row_end = 0
        self.update_screen()

    def set_input(self, text: str):
        self._input.set_text(text)
        self.search_by_input()

    def get_input(self) -> str:
        return self._input.text

    def set_prompt(self, prompt: str):
        self._input.prompt = prompt

    def clear_input(self):
        self._input.clear()
        self.reset_selection()
        self.update_screen()

    def call_func_without_curses(self, func: Callable[[], Any]):
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
        # Enter raw mode. In raw mode, normal line buffering and processing of
        # interrupt, quit, suspend, and flow control keys are turned off. This
        # allows for the use of the hotkey Ctrl-S, which used to be associated
        # with XOFF/XON flow control. Ctrl-S functions as the XOFF command.
        curses.raw()
        curses.cbreak()
        curses.start_color()
        curses.use_default_colors()  # The default color is assigned to -1
        curses.init_pair(1, curses.COLOR_BLUE, -1)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)

        color_pair_index = 3

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
        self.on_update_screen(height=self._height)
        Menu.stdscr.refresh()

    def update_matched_items(self):
        self._matched_item_indices.clear()
        for i, item in enumerate(self.items):
            if self.match_item(self.get_input(), item):
                self._matched_item_indices.append(i)

        num_matched_items = len(self._matched_item_indices)
        if num_matched_items > 0:
            self._selected_row_begin = min(
                self._selected_row_begin, num_matched_items - 1
            )
            self._selected_row_end = min(self._selected_row_end, num_matched_items - 1)
        else:
            self._selected_row_begin = 0
            self._selected_row_end = 0
        self._check_if_item_selection_changed()

        self._last_input = self.get_input()
        self._last_item_count = len(self.items)
        self._last_match_time = time.time()
        self._should_update_matched_items = False
        self._should_update_screen = True

    def reset_selection(self):
        self._selected_row_begin = 0
        self._selected_row_end = 0

    def set_selected_row(self, selected_row: int):
        self._requested_selected_row = selected_row
        self._check_if_item_selection_changed()

    def refresh(self):
        self._should_update_matched_items = True

    # Returns false if we should exit main loop for the current window
    def process_events(self, timeout_ms: int = 0) -> bool:
        assert Menu.stdscr is not None

        if self._closed:
            return False

        if timeout_ms > 0:
            Menu.stdscr.timeout(timeout_ms)
        else:
            Menu.stdscr.timeout(0)

        if self._should_update_matched_items or (
            time.time() > self._last_match_time + 0.1
            and (
                (not self.__search_on_enter and self._last_input != self.get_input())
                or self._last_item_count != len(self.items)
            )
        ):
            self.update_matched_items()

        if self._requested_selected_row >= 0:
            self._selected_row_begin = self._requested_selected_row
            self._selected_row_end = self._requested_selected_row
            self._requested_selected_row = -1

        if self._should_update_screen:
            self._update_screen()
            self._should_update_screen = False

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

            elif ch == "\n" or ch == "\r":
                self.on_enter_pressed()

            elif ch == curses.KEY_UP or ch == 450:  # curses.KEY_A2
                if len(self._matched_item_indices) > 0:
                    self._selected_row_end = max(self._selected_row_end - 1, 0)
                    if not self._multi_select_mode:
                        self._selected_row_begin = self._selected_row_end
                    self.update_screen()
                    self._check_if_item_selection_changed()

            elif ch == curses.KEY_DOWN or ch == 456:  # curses.KEY_C2
                if len(self._matched_item_indices) > 0:
                    self._selected_row_end = min(
                        self._selected_row_end + 1,
                        len(self._matched_item_indices) - 1,
                    )
                    if not self._multi_select_mode:
                        self._selected_row_begin = self._selected_row_end
                    self.update_screen()
                    self._check_if_item_selection_changed()

            elif (
                ch == curses.KEY_LEFT or ch == 452  # curses.KEY_B1
            ) and self._can_scroll_left:
                self._scroll_x = max(self._scroll_x - self._scroll_distance, 0)
                self.update_screen()

            elif (
                ch == curses.KEY_LEFT or ch == 452  # curses.KEY_B3
            ) and "left" in self._hotkeys:
                self._hotkeys["left"].func()

            elif (
                ch == curses.KEY_RIGHT or ch == 454  # curses.KEY_B3
            ) and self._can_scroll_right:
                self._scroll_x += self._scroll_distance
                self.update_screen()

            elif (
                ch == curses.KEY_RIGHT or ch == 454  # curses.KEY_B3
            ) and "right" in self._hotkeys:
                self._hotkeys["right"].func()

            elif ch == curses.KEY_PPAGE or ch == 451:  # curses.KEY_A3
                if len(self._matched_item_indices) > 0:
                    self._selected_row_end = max(
                        self._selected_row_end - self.get_items_per_page(), 0
                    )
                    if not self._multi_select_mode:
                        self._selected_row_begin = self._selected_row_end
                    self.update_screen()
                    self._check_if_item_selection_changed()

            elif ch == curses.KEY_NPAGE or ch == 457:  # curses.KEY_C3
                if len(self._matched_item_indices) > 0:
                    self._selected_row_end = min(
                        self._selected_row_end + self.get_items_per_page(),
                        len(self._matched_item_indices) - 1,
                    )
                    if not self._multi_select_mode:
                        self._selected_row_begin = self._selected_row_end
                    self.update_screen()
                    self._check_if_item_selection_changed()

            elif ch == curses.KEY_HOME or ch == 449:
                if len(self._matched_item_indices) > 0:
                    self._selected_row_end = 0
                    if not self._multi_select_mode:
                        self._selected_row_begin = self._selected_row_end
                    self.update_screen()
                    self._check_if_item_selection_changed()

            elif ch == curses.KEY_END or ch == 455:
                if len(self._matched_item_indices) > 0:
                    self._selected_row_begin = self._selected_row_end = (
                        len(self._matched_item_indices) - 1
                    )
                    if not self._multi_select_mode:
                        self._selected_row_begin = self._selected_row_end
                    self.update_screen()
                    self._check_if_item_selection_changed()

            elif ch == curses.KEY_DC and "delete" in self._hotkeys:
                self._hotkeys["delete"].func()

            elif self._check_ctrl_hotkey(ch):
                pass

            elif self._check_shift_hotkey(ch):
                pass

            elif self._check_alt_hotkey(ch):
                pass

            elif ch == "\x1b":  # escape key
                self.on_escape_pressed()

            elif ch != "\0":
                if self._allow_input:
                    self._input.on_char(ch)
                    self.update_screen()

            self.prev_key = ch

        if ch == -1 and timeout_ms:  # getch() is timed-out
            self._on_idle()

        if self._closed:
            self.on_exit()
            return False
        else:
            return True

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
        key2: Optional[str] = None

        if sys.platform == "win32":
            if isinstance(ch, int):
                if ch >= 0x1A1 and ch <= 0x1BA:
                    key2 = chr(ord("a") + (ch - 0x1A1))
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
                    key2 = chr(ch2)
                    is_alt_hotkey = True

        if key2 == "\n" or key2 == "\r":
            key2 = "enter"

        if key2 is not None:
            htk = "alt+" + key2
            if htk in self._hotkeys:
                logging.debug(f"Hotkey pressed: {htk}")
                self._hotkeys[htk].func()

        return is_alt_hotkey

    def _on_idle(self):
        self.on_idle()

    def on_exit(self):
        pass

    def on_idle(self):
        pass

    def _exec(self):
        self.is_cancelled = False
        self._closed = False
        self.update_screen()
        self.on_created()
        self.on_main_loop()
        while self.process_events(timeout_ms=1000):
            self.on_main_loop()

    def get_selected_index(self):
        if self.is_cancelled:
            return -1
        elif len(self._matched_item_indices) > 0:
            return self._matched_item_indices[self._selected_row_end]
        else:
            return -1

    def get_text(self) -> Optional[str]:
        if self.is_cancelled:
            return None
        else:
            return self._input.text

    def get_items_per_page(self):
        return self._height - 3

    class DrawTextResult(NamedTuple):
        next_i: int
        can_scroll_left: bool
        can_scroll_right: bool

    def draw_text(
        self,
        row: int,
        col: int,
        s: str,
        color_pair=0,
        wrap_text=False,
        scroll_x=0,
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
            Menu.stdscr.attron(curses.color_pair(2))
            Menu.stdscr.addstr(row, col, "<")
            Menu.stdscr.attroff(curses.color_pair(2))
            x = col + 1
        else:
            x = col

        if color_pair > 0:
            Menu.stdscr.attron(curses.color_pair(color_pair))

        y = row
        last_row_index = row
        can_scroll_right = False
        for i, ch in enumerate(s):
            try:
                Menu.stdscr.addstr(y, x, ch)
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
                        Menu.stdscr.attron(curses.color_pair(2))
                        Menu.stdscr.addstr(row, self._width - 1, ">")
                        Menu.stdscr.attroff(curses.color_pair(2))
                        can_scroll_right = True
                    break

            last_row_index = y

        if color_pair > 0:
            if y < self._height:
                space_len = self._width - x - 1
                if space_len > 0:
                    try:
                        Menu.stdscr.addstr(y, x, " " * space_len)
                    except curses.error:
                        # addch() returns an error because it tries to wrap to
                        # the next line after adding a character, but this
                        # behavior is expected.
                        pass
            Menu.stdscr.attroff(curses.color_pair(color_pair))

        return Menu.DrawTextResult(
            next_i=last_row_index,
            can_scroll_left=scroll_x > 0,
            can_scroll_right=can_scroll_right,
        )

    def on_update_screen(self, height: int):
        assert Menu.stdscr is not None

        if height < 0:
            height = self._height

        # Render input widget
        draw_input_result = self._input.draw_input(
            Menu.stdscr,
            0,
            show_enter_symbol=self.__should_trigger_search(),
        )

        # Get matched scripts
        row = draw_input_result.last_y + 2
        items_per_page = self.get_items_per_page()

        page_index = self._selected_row_end // items_per_page
        selected_j = self._selected_row_end % items_per_page

        page_index_begin = self._selected_row_begin // items_per_page
        if page_index_begin < page_index:
            selected_i = 0
        elif page_index_begin > page_index:
            selected_i = items_per_page - 1
        else:
            selected_i = self._selected_row_begin % items_per_page
        if selected_i > selected_j:
            selected_i, selected_j = selected_j, selected_i

        start_index = page_index * items_per_page
        end_index = start_index + items_per_page
        indices_in_page = self._matched_item_indices[start_index:end_index]
        if len(indices_in_page):
            row_number_width = max(len(str(i + 1)) for i in indices_in_page)
        else:
            row_number_width = 0

        self._text_overflow = False
        next_i = 0
        self._can_scroll_left = False
        self._can_scroll_right = False
        for i, item_index in enumerate(indices_in_page):
            if row >= next_i:
                is_item_selected = i >= selected_i and i <= selected_j
                item_text = str(self.items[item_index])

                # Highlight text by regex
                color = "white"
                if self._highlight is not None:
                    for patt, c in self._highlight.items():
                        if re.search(patt, item_text):
                            color = c
                if is_item_selected:
                    color = color.upper()
                color_pair = Menu.color_pair_map[color]

                # Draw row number
                row_number = f"{item_index + 1}"
                self.draw_text(
                    row,
                    0,
                    row_number.rjust(row_number_width),
                )

                # Draw item text
                draw_text_result = self.draw_text(
                    row,
                    row_number_width + 1,
                    item_text,
                    wrap_text=self._wrap_text and is_item_selected,
                    color_pair=color_pair,
                    scroll_x=self._scroll_x,
                )
                next_i = draw_text_result.next_i + 1
                self._scroll_distance = self._width - row_number_width - 2
                if draw_text_result.can_scroll_left:
                    self._can_scroll_left = True
                if draw_text_result.can_scroll_right:
                    self._can_scroll_right = True

            row += 1
            if row >= height:
                break

        # Draw status bar
        a = self.get_status_bar_text()
        b = " [%d/%d]" % (
            self._selected_row_end + 1,
            len(self._matched_item_indices),
        )
        self.draw_text(
            row=self._height - 1,
            col=0,
            s=f"{a[:self._width - len(b)]:<{self._width - len(b)}}{b:>{len(b)}}",
            color_pair=Menu.color_pair_map["WHITE"],
        )

        # Move cursor
        try:
            Menu.stdscr.move(draw_input_result.cursor_y, draw_input_result.cursor_x)
        except curses.error:
            pass

    def get_status_bar_text(self) -> str:
        columns: List[str] = []
        if self._multi_select_mode:
            columns.append("multi_select_mode")
        if self._message:
            columns.append(self._message)
        columns.append("command_palette (^p)")
        return " | ".join(columns)

    def get_selected_item(self, ignore_cancellation=False) -> Optional[T]:
        if not ignore_cancellation and self.is_cancelled:
            return None
        elif len(self._matched_item_indices) > 0:
            item_index = self._matched_item_indices[self._selected_row_end]
            return self.items[item_index]
        else:
            return None

    def get_selected_items(self) -> Iterator[T]:
        if len(self._matched_item_indices) > 0:
            i = self._selected_row_begin
            j = self._selected_row_end
            if i > j:
                i, j = j, i
            item_indices = self._matched_item_indices[i : j + 1]
            for item_index in item_indices:
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
        return self.__search_on_enter and self.get_input() != self._last_input

    def search_by_input(self) -> bool:
        if self.__should_trigger_search():
            self.update_matched_items()
            return True
        else:
            return False

    def on_enter_pressed(self):
        if self.search_by_input():
            return

        else:
            item = self.get_selected_item()
            if item is not None:
                if self._on_item_selected is not None:
                    self.call_func_without_curses(
                        lambda item=item: self._on_item_selected(item)
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
        if self._selected_row_end < len(self._matched_item_indices):
            item_index = self._matched_item_indices[self._selected_row_end]
            selected = self.items[item_index]
        else:
            selected = None

        if selected != self._last_selected_item or self._last_input != self.get_input():
            self.on_item_selection_changed(selected)
        self._last_selected_item = selected

    def on_item_selection_changed(self, item: Optional[T]):
        pass

    def set_message(self, message: Optional[str] = None):
        self._message = message
        self.update_screen()

    def _palette(self):
        self._command_palette_menu.exec()
        hotkey = self._command_palette_menu.get_selected_item()
        if hotkey is not None:
            hotkey.func()
        self.update_screen()

    def update_screen(self):
        self._should_update_screen = True

    def _toggle_multi_select(self):
        self._multi_select_mode = not self._multi_select_mode
        self.update_screen()
