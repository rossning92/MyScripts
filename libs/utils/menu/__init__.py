import curses
import curses.ascii
import logging
import os
import re
import subprocess
import sys
import tempfile
import time
from io import StringIO
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
    Tuple,
    TypeVar,
    Union,
)

from _shutil import get_hotkey_abbr

from utils.clamp import clamp
from utils.clip import get_clip, set_clip
from utils.editor import edit_text
from utils.jsonutil import load_json, save_json
from utils.slugify import slugify

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


class _TextInput:
    def __init__(self, prompt="", prompt_color="white", text="", ascii_only=False):
        self.prompt = prompt
        self.prompt_color = prompt_color
        self.text = text
        self.set_text(text)
        self.ascii_only = ascii_only
        self.selected_text: str = ""

    def set_text(self, text):
        self.text = text
        self.selected_text = ""
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
        stdscr.addstr(
            row,
            0,
            self.prompt + ":",
            Menu.color_name_to_attr(self.prompt_color),
        )

        cursor_y, cursor_x = y, x = Menu.stdscr.getyx()  # type: ignore
        x += 1  # add a space between label and text input

        try:
            stdscr.addstr(y, x, self.text[: self.caret_pos])
            cursor_y, cursor_x = Menu.stdscr.getyx()  # type: ignore

            s = self.text[self.caret_pos :]
            if show_enter_symbol:
                s += " [search]"

            stdscr.addstr(cursor_y, cursor_x, s)

            if self.selected_text:
                y, x = Menu.stdscr.getyx()  # type: ignore
                _, max_x = Menu.stdscr.getmaxyx()  # type: ignore
                max_text_len = max_x - x
                stdscr.addstr(
                    y,
                    x,
                    self.selected_text[:max_text_len],
                    Menu.color_name_to_attr("blue"),
                )

        except curses.error:
            pass

        return _TextInput.DrawInputResult(
            cursor_x=cursor_x, cursor_y=cursor_y, last_x=x, last_y=y
        )

    def clear(self):
        self.text = ""
        self.selected_text = ""
        self.caret_pos = 0

    def on_char(self, ch):
        if ch == curses.ERR:
            pass
        elif ch == curses.KEY_LEFT or ch == 452:  # curses.KEY_B1
            self.caret_pos = max(self.caret_pos - 1, 0)
        elif ch == curses.KEY_RIGHT or ch == 454:  # curses.KEY_B3
            self.caret_pos = min(self.caret_pos + 1, len(self.text))
        elif _is_backspace_key(ch):
            self.selected_text = ""
            if self.caret_pos > 0:

                self.text = (
                    self.text[: self.caret_pos - 1] + self.text[self.caret_pos :]
                )
                self.caret_pos = max(self.caret_pos - 1, 0)

        elif ch == curses.ascii.ctrl("u"):
            self.clear()
        elif ch == curses.ascii.ctrl("w"):
            position_after_last_space = max(0, self.text.rstrip().rfind(" ") + 1)
            self.text = self.text[:position_after_last_space]
            self.caret_pos = len(self.text)
        elif ch == curses.ascii.ctrl("a"):
            self.caret_pos = 0
        # HACK: Workaround for single and double quote on Windows
        elif ch == 530 and sys.platform == "win32":
            self._on_char("'")
        elif ch == 460 and sys.platform == "win32":
            self._on_char('"')
        elif isinstance(ch, str):
            self._on_char(ch)

    def _on_char(self, ch: str):
        if not self.ascii_only or (self.ascii_only and re.match("[\x00-\x7f]", ch)):
            self.insert_text(ch)

    def insert_text(self, text: str):
        self.text = self.text[: self.caret_pos] + text + self.text[self.caret_pos :]
        self.caret_pos += len(text)
        self.selected_text = ""


T = TypeVar("T")
R = TypeVar("R")


class Menu(Generic[T]):
    _should_update_screen = False
    color_pair_map: Dict[str, int] = {}
    log_handler: Optional[logging.StreamHandler] = None
    logger: Optional[logging.Logger] = None
    stdscr = None

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
        prompt_color="white",
        follow=False,
    ):
        self.close_on_selection: bool = close_on_selection
        self.is_cancelled: bool = False
        self.items: List[T] = items if items is not None else []
        self.last_key_pressed_timestamp: float = 0.0

        self._height: int = -1

        self.__input = _TextInput(
            prompt=prompt,
            text=text if text else "",
            ascii_only=ascii_only,
            prompt_color=prompt_color,
        )

        self.__last_key: Union[int, str] = -1
        self.__allow_input: bool = allow_input
        self.__cancellable: bool = cancellable
        self.__closed: bool = False
        self.__debug = debug
        self.__empty_lines: int = 0

        self.__highlight = highlight
        self.__is_stdscr_owner: Optional[bool] = None
        self.__last_input: Optional[str] = None
        self.__last_item_count = 0
        self.__last_selected_item: Optional[T] = None
        self.__line_number = line_number
        self.__matched_item_indices: List[int] = []
        self.__message: Optional[str] = None
        self.__num_rendered_items: int = 0
        self.__on_item_selected = on_item_selected
        self.__search_history: List[str] = []
        self.__width: int = -1
        self.__wrap_text: bool = wrap_text

        # Search
        self.__search_mode = search_mode
        self.__search_on_enter: bool = search_on_enter
        self.__fuzzy_search = fuzzy_search

        # Scroll
        self.__scroll_y: int = 0
        self.__scroll_x = 0
        self.__can_scroll = False

        # Selection
        self.__follow = follow
        self.__selected_row_begin: int = selected_index
        self.__selected_row_end: int = selected_index
        self.__multi_select_mode: bool = False

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

        # Commands and hotkeys
        self.__hotkeys: Dict[str, _Command] = {}
        self.__custom_commands: List[_Command] = []
        if enable_command_palette:
            self.add_command(self.__ask_selection, hotkey="!")
            self.add_command(self.__command_palette, hotkey="ctrl+p")
            self.add_command(self.__edit_text_in_external_editor, hotkey="ctrl+e")
            self.add_command(self.__goto, hotkey="ctrl+g")
            self.add_command(self.__logs, hotkey="alt+l")
            self.add_command(self.__prev_search_history, hotkey="alt+u")
            self.add_command(self.__select_all)
            self.add_command(self.__toggle_multi_select, hotkey="ctrl+x")
            self.add_command(self.__toggle_wrap, hotkey="alt+z")
            self.add_command(self.paste, hotkey="ctrl+v")
            self.add_command(self.voice_input, hotkey="alt+v")
            self.add_command(self.voice_input, hotkey="space space")
            self.add_command(self.yank, hotkey="ctrl+y")

            for item in self.items:
                if hasattr(item, "hotkey"):
                    hotkey = item.__dict__["hotkey"]
                    if hotkey:
                        self.add_command(
                            lambda item=item: self.__on_item_hotkey(item),
                            hotkey=hotkey,
                        )

    def __goto(self):
        selected = self.get_selected_item()
        if selected:
            from ext.contextmenu import ContextMenu

            ContextMenu(param=str(selected)).exec()

    def __logs(self):
        if Menu.log_handler:
            from .textmenu import TextMenu

            TextMenu(text=Menu.log_handler.stream.getvalue(), prompt="Logs").exec()

    @staticmethod
    def __setup_logging():
        Menu.log_handler = logging.StreamHandler(StringIO())
        Menu.logger = logging.getLogger()
        Menu.logger.setLevel(logging.DEBUG)
        for handler in Menu.logger.handlers:
            Menu.logger.removeHandler(handler)
        Menu.logger.addHandler(Menu.log_handler)

    @staticmethod
    def __teardown_logging():
        if Menu.logger and Menu.log_handler:
            Menu.logger.removeHandler(Menu.log_handler)
            Menu.log_handler.close()

    def __enter__(self):
        if self.__is_stdscr_owner:
            raise Exception("Using with-clause on Menu object twice is not allowed")
        self.__is_stdscr_owner = Menu.stdscr is None
        if self.__is_stdscr_owner:
            Menu.__setup_logging()
            Menu.init_curses()

    def __exit__(self, exc_type, exc_val, traceback):
        if self.__is_stdscr_owner:
            Menu.destroy_curses()
            Menu.__teardown_logging()
        else:
            Menu._should_update_screen = True
        self.__is_stdscr_owner = False
        self.on_close()

    def voice_input(self):
        from ai.openai.speech_to_text import convert_audio_to_text

        from utils.menu.asynctaskmenu import AsyncTaskMenu
        from utils.menu.recordmenu import RecordMenu

        record_menu = RecordMenu()
        record_menu.exec()
        out_file = record_menu.get_output_file()
        if not out_file:
            return

        stt_menu = AsyncTaskMenu(
            lambda: convert_audio_to_text(file=out_file),
            prompt="(Converting audio to text...)",
        )
        try:
            stt_menu.exec()
        except ValueError as e:
            self.set_message(f"ERROR: {e}")
            return

        os.remove(out_file)
        text = stt_menu.get_result()
        if text:
            self.insert_text(text)
            if not record_menu.space_pressed:
                self.on_enter_pressed()

    def __select_all(self):
        self.set_selection(0, -1)

    def __prev_search_history(self):
        if len(self.__search_history) > 0:
            last_input = self.__search_history.pop(0)
            self.set_message(last_input)
            self.set_input(last_input, save_search_history=False)

    def yank(self):
        set_clip(self.__get_selected_lines())
        self.set_message("copied")

    def paste(self) -> bool:
        text = get_clip()
        if not text:
            return False
        self.insert_text(text)
        self.update_screen()
        return True

    def add_command(
        self, func: Callable, hotkey: Optional[str] = None, name: Optional[str] = None
    ) -> _Command:
        command = _Command(hotkey=hotkey, func=func, name=name)
        self.__custom_commands.append(command)

        if hotkey is not None:
            self.__hotkeys[hotkey] = command

        return command

    def delete_commands_if(self, condition: Callable[[_Command], bool]):
        for cmd in self.__custom_commands[:]:  # Iterate over a copy of the list
            if condition(cmd):
                self.__custom_commands.remove(cmd)

    def get_history_file(self):
        from scripting.path import get_data_dir

        return os.path.join(get_data_dir(), "%s_history.json" % slugify(self.history))

    def match_item(self, patt: str, item: T, index: int) -> int:
        """
        Checks if an item matches a pattern.

        Args:
            patt (str): Pattern to match.
            item (T): Item to be checked.
            index (int): Item index.

        Returns:
            int: rank: greater than 0 if the item matches the pattern, 0 otherwise. Results will be ordered by rank from high to low.
        """

        s = str(item)
        return 1 if _match(s, patt, fuzzy_match=self.__fuzzy_search, index=index) else 0

    def get_item_indices(self):
        if self.__search_mode:
            return self.__matched_item_indices
        else:
            return range(len(self.items))

    def append_item(self, item: T):
        self.items.append(item)
        self.__last_item_count = len(self.items)
        added_index = self.__last_item_count - 1

        # Scroll to bottom if last line is selected
        if self.__search_mode:
            if self.match_item(self.__input.text, item, added_index):
                self.__matched_item_indices.append(added_index)

        self.update_screen()

    def clear_items(self):
        self.items.clear()
        self.__last_item_count = 0
        self.__matched_item_indices.clear()
        self.reset_selection()
        self.update_screen()

    def set_follow(self, follow: bool) -> None:
        self.__follow = follow

    def set_input(self, text: str, save_search_history=True):
        self.__input.set_text(text)
        if self.__search_mode:
            self.search_by_input(save_search_history=save_search_history)
        self.update_screen()

    def insert_text(self, text: str):
        self.__input.insert_text(text)
        self.update_screen()

    def get_input(self) -> str:
        return (
            self.__input.selected_text
            if self.__input.selected_text
            else self.__input.text
        )

    def set_prompt(self, prompt: str):
        self.__input.prompt = prompt
        self.update_screen()

    def clear_input(self, reset_selection=False) -> bool:
        if self.__input.text == "":
            return False

        if self.__search_mode:
            if reset_selection:
                self.set_input("")
                self.reset_selection()
            elif self.__selected_row_end >= 0 and self.__selected_row_end < len(
                self.__matched_item_indices
            ):  # select the same item when filter is removed
                row_number = self.__matched_item_indices[self.__selected_row_end]
                self.set_input("")
                self.set_selected_row(row_number)
            else:
                self.set_input("")
        else:
            self.set_input("")
        return True

    def call_func_without_curses(self, func: Callable[[], R]) -> R:
        Menu.destroy_curses()
        try:
            return func()
        finally:
            Menu.init_curses()

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

        self._height, self.__width = Menu.stdscr.getmaxyx()  # type: ignore

        if sys.platform == "win32":
            Menu.stdscr.clear()
        else:
            # Use erase instead of clear to prevent flickering
            Menu.stdscr.erase()
        self.__on_update_screen(item_y_max=self._height - 1)
        Menu.stdscr.refresh()

    def reset_selection(self):
        self.set_selection(0, 0)

    def set_selected_row(self, selected_row: int):
        self.set_selection(selected_row, selected_row)

    def set_selected_item(self, item: T):
        def try_select_item(item: T) -> bool:
            for i, idx in enumerate(self.get_item_indices()):
                if self.items[idx] == item:
                    self.set_selected_row(i)
                    return True
            return False

        if not try_select_item(item):
            self.clear_input()
            try_select_item(item)

    def set_selection(self, begin_row: int, end_row: int):
        self.__update_matched_items()
        total = len(self.get_item_indices())

        if end_row == -1:
            end_row = total - 1

        if (
            begin_row == self.__selected_row_begin
            and end_row == self.__selected_row_end
        ):
            return

        if begin_row != end_row:
            self.__multi_select_mode = True
        self.__selected_row_begin = begin_row
        self.__selected_row_end = end_row

        if self.__selected_row_begin >= total:
            self.__selected_row_begin = max(0, total - 1)
        if self.__selected_row_end >= total:
            self.__selected_row_end = max(0, total - 1)
        self.__follow = self.__selected_row_end == total - 1
        self._check_if_item_selection_changed()
        self.update_screen()

    def refresh(self):
        self.__update_matched_items(force_update=True)

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

    def on_keyboard_interrupt(self):
        sys.exit(0)

    # Returns True if we should exit main loop for the current window
    def process_events(
        self, timeout_sec: float = 0.0, raise_keyboard_interrupt=False
    ) -> bool:
        assert Menu.stdscr is not None

        if self.__closed:
            return True

        if timeout_sec > 0.0:
            Menu.stdscr.timeout(int(timeout_sec * 1000.0))
        else:
            Menu.stdscr.timeout(0)

        self.__update_matched_items()

        # Update screen
        if self.__should_update_screen or Menu._should_update_screen:
            Menu._should_update_screen = False
            self.__should_update_screen = False
            self._update_screen()

        # Keyboard event
        ch: Union[int, str] = -1
        try:
            ch = Menu.stdscr.get_wch()
        except curses.error:
            pass
        except KeyboardInterrupt:
            if raise_keyboard_interrupt:
                raise
            else:
                self.on_keyboard_interrupt()

        if ch != -1:  # getch() will return -1 when timeout
            if self.__debug:
                if isinstance(ch, str):
                    self.set_message(f"key={repr(ch)}")
                elif isinstance(ch, int):
                    self.set_message(f"key=0x{ch:x}")

            self.last_key_pressed_timestamp = time.time()
            if self.on_char(ch):
                self.update_screen()

            elif ch == curses.ascii.ctrl("c"):
                if raise_keyboard_interrupt:
                    raise KeyboardInterrupt
                else:
                    self.on_keyboard_interrupt()

            elif ch == "@" and "@" in self.__hotkeys:
                self.__hotkeys["@"].func()

            elif ch == " " and self.__input.text == "" and "space" in self.__hotkeys:
                self.__hotkeys["space"].func()

            elif ch == " " and self.__input.text == " ":
                self.set_input("")
                if "space space" in self.__hotkeys:
                    self.__hotkeys["space space"].func()

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
                ch == curses.KEY_LEFT or ch == 452
            ) and "left" in self.__hotkeys:  # curses.KEY_B3
                self.__hotkeys["left"].func()

            elif (
                ch == curses.KEY_LEFT or ch == 452  # curses.KEY_B1
            ) and self.__can_scroll:
                self.__scroll_x = max(self.__scroll_x - self.get_scroll_distance(), 0)
                self.update_screen()

            elif (
                ch == curses.KEY_RIGHT or ch == 454
            ) and "right" in self.__hotkeys:  # curses.KEY_B3
                self.__hotkeys["right"].func()

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

            elif ch == curses.KEY_DC and "delete" in self.__hotkeys:
                self.__hotkeys["delete"].func()

            elif self._check_ctrl_hotkey(ch):
                pass

            elif self._check_shift_hotkey(ch):
                pass

            elif self._check_alt_hotkey(ch):
                pass

            elif (
                sys.platform == "win32"
                and ch == 0x211
                and "alt+enter" in self.__hotkeys
            ):
                self.__hotkeys["alt+enter"].func()

            elif ch == "\x1b":  # escape key
                self.on_escape_pressed()

            elif ch != "\0":
                if self.__allow_input:
                    self.__input.on_char(ch)
                    self.update_screen()

            self.__last_key = ch

        if ch == -1 and timeout_sec > 0.0:  # getch() is timed-out
            self._on_idle()

        if self.__closed:
            self.on_exit()
            return True
        else:
            return False

    def __update_matched_items(self, save_search_history=True, force_update=False):
        if self.__search_mode:
            if (
                force_update
                or self.__should_update_matched_items
                or (
                    time.time() > self.__last_match_time + PROCESS_EVENT_INTERVAL_SEC
                    and (
                        (
                            not self.__search_on_enter
                            and self.__last_input != self.__input.text
                        )
                        or self.__last_item_count != len(self.items)
                    )
                )
                or (len(self.items) < self.__last_item_count)
            ):
                matches: List[Tuple[int, int]] = []  # list of tuple of index and rank
                for i, item in enumerate(self.items):
                    rank = self.match_item(self.__input.text, item, i)
                    if rank > 0:  # match
                        matches.append((i, rank))
                # Sort matches by rank in descending order, preserving order for equal ranks
                matches = sorted(matches, key=lambda x: x[1], reverse=True)
                self.__matched_item_indices[:] = [index for index, _ in matches]

                self.__selected_row_begin = 0
                self.__selected_row_end = 0
                self.__follow = False
                self._check_if_item_selection_changed()

                if save_search_history and self.__last_input is not None:
                    self.__search_history.insert(0, self.__last_input)
                self.__last_input = self.__input.text
                self.__last_item_count = len(self.items)
                self.__last_match_time = time.time()
                self.__should_update_matched_items = False
                self.__should_update_screen = True

                self.on_matched_items_updated()

    def on_escape_pressed(self):
        if "escape" in self.__hotkeys:
            logging.debug("Hotkey pressed: escape")
            self.__hotkeys["escape"].func()
            return True
        else:
            if self.__cancellable:
                self.cancel()
            else:
                self.__input.clear()
                self.update_screen()

    def on_matched_items_updated(self):
        pass

    def _check_ctrl_hotkey(self, ch: Union[str, int]) -> bool:
        if curses.ascii.isctrl(ch):
            htk = "ctrl+" + curses.ascii.unctrl(ch)[-1].lower()
            if htk in self.__hotkeys:
                logging.debug(f"Hotkey pressed: {htk}")
                self.__hotkeys[htk].func()
                return True
        return False

    def _check_shift_hotkey(self, ch: Union[str, int]) -> bool:
        if isinstance(ch, str):
            if ch in self.__hotkeys:
                self.__hotkeys[ch].func()
                return True
            elif len(ch) == 1 and ch.isupper():
                htk = "shift+" + ch.lower()
                if htk in self.__hotkeys:
                    logging.debug(f"Hotkey pressed: {htk}")
                    self.__hotkeys[htk].func()
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
            if htk in self.__hotkeys:
                logging.debug(f"Hotkey pressed: {htk}")
                self.__hotkeys[htk].func()
            elif key_name == "enter":  # alt + enter
                self.__input.on_char("\n")  # new line
                self.update_screen()

        return is_alt_hotkey

    def _on_idle(self):
        self.on_idle()

    def on_exit(self):
        pass

    def on_idle(self):
        pass

    def on_close(self):
        pass

    def _reset_state(self):
        self.is_cancelled = False
        self.__closed = False

    def _exec(self):
        self._reset_state()
        self.update_screen()
        self.on_created()
        self.on_main_loop()
        while not self.process_events(timeout_sec=PROCESS_EVENT_INTERVAL_SEC):
            self.on_main_loop()
        self.on_close()

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
            return self.get_input()

    def get_items_per_page(self):
        return self.__num_rendered_items + self.__empty_lines

    class DrawTextResult(NamedTuple):
        last_y: int
        can_scroll_left: bool
        can_scroll_right: bool

    @staticmethod
    def color_name_to_attr(color: str) -> int:
        attr = curses.color_pair(Menu.color_pair_map[color])
        if color == "gray":
            attr |= curses.A_DIM
        return attr

    def draw_text(
        self,
        row: int,
        col: int,
        s: str,
        ymax: int,  # max y (exclusive).
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

        if row >= ymax:
            raise Exception(
                f'row should be smaller than ymax, but row={row} yamx={ymax} s="{s}"'
            )

        s = s[scroll_x:]

        # Draw left arrow
        if scroll_x > 0:
            Menu.stdscr.addstr(row, col, "<", Menu.color_name_to_attr("WHITE"))
            x = col + 1
        else:
            x = col

        last_row_index = y = row
        can_scroll_right = False
        attr = Menu.color_name_to_attr(color)
        if bold:
            attr |= curses.A_BOLD
        i = 0
        while i < len(s):
            ch = s[i]
            if ch == "\\":
                if s[i : i + 10] == r"\x1b[1;31m":
                    i += 10
                    attr = Menu.color_name_to_attr("red") | curses.A_BOLD
                    continue
                elif s[i : i + 7] == r"\033[0m":
                    i += 7
                    attr = Menu.color_name_to_attr(color)
                    continue

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
                if y >= ymax:
                    # If text overflows outside of the screen, set last_row_index to screen height.
                    last_row_index = ymax
                    break
                elif y > last_y:
                    x = col
            else:
                if y > last_y:
                    if i < len(s) - 1:
                        last_row_index = row
                        Menu.stdscr.addstr(
                            row,
                            self.__width - 1,
                            ">",
                            Menu.color_name_to_attr("WHITE"),
                        )
                        can_scroll_right = True
                    break
            if x > col:
                last_row_index = y

            i += 1

        return Menu.DrawTextResult(
            last_y=last_row_index,
            can_scroll_left=scroll_x > 0,
            can_scroll_right=can_scroll_right,
        )

    def get_item_text(self, item: T) -> str:
        return str(item)

    def get_item_color(self, item: T) -> str:
        return "white"

    def goto_line(self, line: int):
        self.__scroll_y = line

    def __on_update_screen(self, item_y_max: int):
        assert Menu.stdscr is not None

        # Render input widget
        draw_input_result = self.__input.draw_input(
            Menu.stdscr,
            0,
            show_enter_symbol=self.__should_trigger_search(),
        )

        # Get matched scripts
        item_y = draw_input_result.last_y + 2

        # Auto select last item
        item_indices = self.get_item_indices()
        total_items = len(item_indices)
        if self.__follow:
            if not self.__multi_select_mode:
                self.__selected_row_begin = total_items - 1
            self.__selected_row_end = total_items - 1
        else:
            self.__selected_row_begin = clamp(
                self.__selected_row_begin, 0, total_items - 1
            )
            self.__selected_row_end = clamp(self.__selected_row_end, 0, total_items - 1)

        # Draw status bar
        status_bar_text = self.get_status_text()
        lines = status_bar_text.splitlines()
        if len(lines) < self._height:
            for i, status_line in enumerate(lines):
                parts = status_line.split("\t", maxsplit=1)
                if len(parts) == 1:
                    status_line = parts[0]
                else:
                    status_bar_text, b = parts
                    status_line = f"{status_bar_text[:self.__width - len(b)]:<{self.__width - len(b)}}{b:>{len(b)}}"

                self.draw_text(
                    row=self._height - len(lines) + i,
                    col=0,
                    s=status_line,
                    color="blue",
                    ymax=self._height,
                )
            item_y_max -= len(lines) - 1

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
            line_number_width = len(self.get_line_number_text(item_indices[-1]))
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

            # Item color
            color = self.get_item_color(item)
            if self.__highlight is not None:
                for patt, c in self.__highlight.items():
                    if re.search(patt, item_text):
                        color = c

            # Draw item
            draw_text_result = self.draw_text(
                item_y,
                line_number_width + (GUTTER_SIZE if self.__line_number else 0),
                item_text,
                wrap_text=self.__wrap_text,
                color=color.upper() if is_item_selected else color,
                scroll_x=self.__scroll_x,
                ymax=item_y_max,
            )

            # Draw line number
            if self.__line_number:
                line_number_text = self.get_line_number_text(item_index)
                line_number_color = "WHITE" if is_item_selected else "gray"
                self.draw_text(
                    item_y,
                    0,
                    line_number_text.rjust(line_number_width) + (" " * GUTTER_SIZE),
                    color=line_number_color,
                    ymax=item_y_max,
                )

                # Draw gutter
                for y in range(
                    item_y + 1, min(draw_text_result.last_y + 1, item_y_max - 1)
                ):
                    self.draw_text(
                        y,
                        0,
                        " " * (line_number_width + GUTTER_SIZE),
                        color=line_number_color,
                        ymax=item_y_max,
                    )

            increments = draw_text_result.last_y + 1 - item_y

            # Ensure the selected item text is fully visible on the screen.
            if (
                self.__selected_row_end == matched_item_index
                and item_y + increments >= item_y_max
            ):
                self.__scroll_y = max(self.__scroll_y - 1, 0)
                self.update_screen()

            if self.__wrap_text:
                matched_item_index += 1
            else:
                matched_item_index += increments

            item_y += increments

            self.__empty_lines = max(0, item_y_max - draw_text_result.last_y - 1)

            if draw_text_result.can_scroll_left or draw_text_result.can_scroll_right:
                self.__can_scroll = True

        if items_per_page != self.get_items_per_page():
            self.update_screen()

        # Move cursor
        try:
            Menu.stdscr.move(draw_input_result.cursor_y, draw_input_result.cursor_x)
        except curses.error:
            pass

    def get_scroll_distance(self) -> int:
        return 10

    def get_status_text(self) -> str:
        status = ""
        if self.__message:
            status += self.__message
        status += "\t"
        item_indices = self.get_item_indices()
        if len(item_indices) > 0:
            current_position = self.__selected_row_end + 1
            total_items = len(item_indices)
            indicators = []
            if self.__multi_select_mode:
                indicators.append("MultiSel")
            if self.__follow:
                indicators.append("Follow")
            indicators.append(f"{current_position}/{total_items}")
            status += " ".join(indicators)
        return status

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

    def on_char(self, ch: Union[int, str]):
        if ch == "\t":
            return self.on_tab_pressed()

        elif type(ch) is str and ch in self.__hotkeys:
            self.__hotkeys[ch].func()
            return True

        else:
            return False

    def __should_trigger_search(self) -> bool:
        if self.__search_mode:
            return self.__search_on_enter and self.__input.text != self.__last_input
        else:
            return False

    def search_by_input(self, save_search_history=True) -> bool:
        if self.__should_trigger_search():
            self.__update_matched_items(
                save_search_history=save_search_history, force_update=True
            )
            return True
        else:
            return False

    def on_enter_pressed(self):
        if self.search_by_input():
            return

        else:
            item = self.get_selected_item()
            if item is not None:
                self.on_item_selected(item)
            if self.close_on_selection:
                self.close()
            else:
                self.update_screen()

    def on_item_selected(self, item: T):
        on_item_selected = self.__on_item_selected
        if on_item_selected is not None:
            self.call_func_without_curses(lambda item=item: on_item_selected(item))

    def on_tab_pressed(self) -> bool:
        if "tab" in self.__hotkeys:
            self.__hotkeys["tab"].func()
            return True
        else:
            item = self.get_selected_item()
            if item is not None:
                self.set_input("%s" % item)
            return True

    def on_main_loop(self):
        pass

    def on_created(self):
        pass

    def close(self):
        self.__closed = True

    def is_closed(self):
        return self.__closed

    def cancel(self):
        self.is_cancelled = True
        self.__closed = True

    def _check_if_item_selection_changed(self):
        selected = None
        item_indices = self.get_item_indices()
        item_index = -1
        if self.__selected_row_end < len(item_indices):
            item_index = item_indices[self.__selected_row_end]
            if item_index < len(self.items):
                selected = self.items[item_index]

        if (
            selected != self.__last_selected_item
            or self.__last_input != self.__input.text
        ) and not _is_backspace_key(self.__last_key):
            self.on_item_selection_changed(selected, i=item_index)
            self.__input.selected_text = (
                selected
                if self.__search_mode
                and not self.__search_on_enter
                and isinstance(selected, str)
                else ""
            )
            self.update_screen()
        self.__last_selected_item = selected

    def on_item_selection_changed(self, item: Optional[T], i: int):
        pass

    def set_message(self, message: Optional[str] = None):
        if message:
            self.__message = message
        else:
            message = None
        logging.info(f"set_message: {message}")
        self.update_screen()

    def __edit_text_in_external_editor(self):
        text = self.__input.text
        new_text = self.call_func_without_curses(lambda: edit_text(text))
        self.set_input(new_text)
        if new_text != text:
            self.on_enter_pressed()

    def __command_palette(self):
        menu = Menu(
            prompt="cmd",
            items=self.__custom_commands,
            enable_command_palette=False,
        )
        menu.exec()
        hotkey = menu.get_selected_item()
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
        i = self.items.index(item)
        self.set_selection(i, i)

        if self.close_on_selection:
            self.close()
        else:
            self.update_screen()

    def get_row_count(self):
        return len(self.__matched_item_indices)

    def get_line_number_text(self, item_index: int) -> str:
        return f"{item_index + 1}"

    def __get_selected_lines(self) -> str:
        selected_items = self.get_selected_items()
        return "\n".join([str(x) for x in selected_items])

    def __ask_selection(self):
        selected_lines = self.__get_selected_lines()
        if selected_lines:
            with tempfile.NamedTemporaryFile(
                mode="w+", delete=False, suffix=".txt", encoding="utf-8"
            ) as f:
                f.write(selected_lines)
                tmpfile = f.name
            subprocess.run(["start_script", "r/ML/gpt/ask.py", tmpfile])
