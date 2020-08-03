import curses
import curses.ascii
import threading
import time
import re
import signal
from _shutil import *


class ListWindow:
    def __init__(self, items):
        self.items = items
        self.cur_input = ""
        self.caret_pos = 0
        self.last_update = 0
        self.exit = False
        self.input_stack = []
        self.selection = None
        self.match_indices = range(len(items))

        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(1)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_YELLOW)
        self.stdscr.nodelay(False)

    def update_screen(self):
        height, width = self.stdscr.getmaxyx()
        self.stdscr.clear()

        items = [self.items[i] for i in self.match_indices]
        items = items[: height - 1]

        for i, item in enumerate(items):
            self.stdscr.addstr(i, 0, item)

        # The user input is display at the bottom of the screen
        self.stdscr.addstr(height - 1, 0, self.cur_input)
        self.stdscr.move(height - 1, self.caret_pos)

        self.stdscr.refresh()

    def update_input(self):
        text_changed = False
        ch = self.stdscr.getch()

        if ch == curses.ERR:
            pass
        elif ch == curses.KEY_LEFT:
            self.caret_pos = max(self.caret_pos - 1, 0)
        elif ch == curses.KEY_RIGHT:
            self.caret_pos = min(self.caret_pos + 1, len(self.cur_input))
        elif ch == ord("\b"):
            self.cur_input = (
                self.cur_input[: self.caret_pos - 1] + self.cur_input[self.caret_pos :]
            )
            self.caret_pos = max(self.caret_pos - 1, 0)
            text_changed = True
        elif ch == curses.ascii.ctrl(ord("c")):
            if len(self.input_stack) > 0:
                self.cur_input = self.input_stack.pop()
                self.caret_pos = len(self.cur_input)
            else:
                self.cur_input = ""
                self.caret_pos = 0
                text_changed = True
        elif ch == curses.ascii.ctrl(ord("w")):
            self.exit = True
        elif ch == ord("\n"):
            self.input_stack.append(self.cur_input)
            self.on_item_selected()
            self.cur_input = ""
            self.caret_pos = 0
        else:
            self.cur_input = (
                self.cur_input[: self.caret_pos]
                + chr(ch)
                + self.cur_input[self.caret_pos :]
            )
            self.caret_pos += 1
            text_changed = True

        if text_changed:
            self.on_text_changed(self.cur_input)

    def on_item_selected(self):
        self.selection = self.match_indices[0]

    def on_text_changed(self, text):
        self.match_indices = [
            i for i, x in enumerate(self.items) if self.cur_input.lower() in x.lower()
        ]

    def update(self):
        self.update_screen()
        self.update_input()

    def exec(self):
        while True:
            if self.exit:
                return None

            if self.selection is not None:
                return self.selection

            self.update()


class InputWindow:
    def __init__(self, on_text_changed=None):
        self.cur_input = ""
        self.caret_pos = 0
        self.on_text_changed = on_text_changed
        self.last_update = 0
        self.block_mode = False
        self.exit = False
        self.input_stack = []

        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(1)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_YELLOW)
        self.stdscr.nodelay(True)

    def update_screen2(self):
        pass

    def update_screen(self):
        height, width = self.stdscr.getmaxyx()
        self.stdscr.clear()

        self.update_screen2()

        # Input text at bottom left
        self.stdscr.addstr(height - 1, 0, self.cur_input)
        self.stdscr.move(height - 1, self.caret_pos)

        self.stdscr.refresh()

    def update_input(self, stdscr):
        while True:
            text_changed = False
            ch = stdscr.getch()

            if ch == curses.ERR:
                break
            elif ch == curses.KEY_LEFT:
                self.caret_pos = max(self.caret_pos - 1, 0)
            elif ch == curses.KEY_RIGHT:
                self.caret_pos = min(self.caret_pos + 1, len(self.cur_input))
            elif ch == ord("\b"):
                self.cur_input = (
                    self.cur_input[: self.caret_pos - 1]
                    + self.cur_input[self.caret_pos :]
                )
                self.caret_pos = max(self.caret_pos - 1, 0)
                text_changed = True
            elif ch == curses.ascii.ctrl(ord("c")):
                if len(self.input_stack) > 0:
                    self.cur_input = self.input_stack.pop()
                    self.caret_pos = len(self.cur_input)
                else:
                    self.cur_input = ""
                    self.caret_pos = 0
                    text_changed = True
            elif ch == curses.ascii.ctrl(ord("w")):
                self.exit = True
            elif ch == ord("\n"):
                self.input_stack.append(self.cur_input)
                self.cur_input = ""
                self.caret_pos = 0
            else:
                self.cur_input = (
                    self.cur_input[: self.caret_pos]
                    + chr(ch)
                    + self.cur_input[self.caret_pos :]
                )
                self.caret_pos += 1
                text_changed = True

            if text_changed and self.on_text_changed:
                self.on_text_changed(self.cur_input)

            if self.block_mode:
                break

    def update(self):
        cur_time = time.time()
        if cur_time > self.last_update + 0.5 or self.block_mode:
            self.last_update = cur_time

            self.update_input(self.stdscr)
            self.update_screen()

    def exec(self):
        self.set_block_mode(True)
        self.update_screen()
        while True:
            if self.exit:
                return
            self.update()

    def set_block_mode(self, block_mode):
        self.block_mode = block_mode
        self.stdscr.nodelay(not block_mode)


class FilterWindow(InputWindow):
    def __init__(self, args):
        super().__init__()

        self.lines = []
        self.ps = check_output2(args)
        for l in self.ps.readlines():
            self.lines.append(l.decode(errors="replace"))
            self.update()

    def update_screen2(self):
        height, width = self.stdscr.getmaxyx()

        filtered_lines = [l for l in self.lines if self.cur_input.lower() in l.lower()]
        n = min(len(filtered_lines), height - 1)
        for i in range(n):
            self.stdscr.addstr(i, 0, filtered_lines[i])


class ListWindowAsync:
    def __init__(self, lines=None, on_text_changed=None, on_item_selected=None):
        self.lines = lines
        self.cur_page = 0
        self.cur_input = ""
        self._cond = threading.Condition()
        self.on_text_changed = on_text_changed
        self.on_item_selected = on_item_selected
        self.last_update = 0
        self.select_mode = False
        self.search_str = ""
        self.caret_pos = 0
        self.block_mode = False
        self.exit = False

        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(1)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_YELLOW)
        self.stdscr.nodelay(True)
        # self.stdscr.scrollok(1)

    def update_screen(self, stdscr):
        height, width = stdscr.getmaxyx()
        stdscr.clear()

        n = len(self.lines)
        start_line = self.cur_page * (height - 1)
        if self.cur_page * (height - 1) > n:
            self.cur_page = 0

        for i in range(height - 1):
            if i + start_line >= n:
                break

            idx = start_line + i
            line = self.lines[idx]
            line = "%d " % idx + line
            line = line.replace("\t", "    ")  # replace tab with space
            line = line[:width]

            # Highlight cur_input
            if self.cur_input:
                match = [
                    (m.start(), m.end()) for m in re.finditer(self.cur_input, line)
                ]
            else:
                match = None

            try:  # HACK: ignore exception on addstr
                if match:
                    substr = line[0 : match[0][0]]
                    stdscr.addstr(i, 0, substr)

                    for j in range(len(match)):
                        stdscr.attron(curses.color_pair(3))
                        substr = line[match[j][0] : match[j][1]]
                        stdscr.addstr(i, match[j][0], substr)
                        stdscr.attroff(curses.color_pair(3))

                        end_pos = match[j + 1][0] if j < len(match) - 1 else None
                        substr = line[match[j][1] : end_pos]
                        stdscr.addstr(i, match[j][1], substr)
                else:
                    stdscr.addstr(i, 0, line)
            except:
                pass

        # stdscr.attron(curses.color_pair(2))
        status_text = "[%d / %d]" % (self.cur_page, len(self.lines) // (height - 1))
        stdscr.insstr(height - 1, width - len(status_text), status_text)

        stdscr.addstr(height - 1, 0, self.cur_input)
        stdscr.move(height - 1, self.caret_pos)
        # stdscr.attroff(curses.color_pair(2))

        stdscr.refresh()

    def update_input(self, stdscr):
        height, width = stdscr.getmaxyx()

        max_page = len(self.lines) // (height - 1)

        while True:
            text_changed = False

            ch = stdscr.getch()

            if ch == curses.ERR:
                break
            elif ch == curses.KEY_RESIZE:
                # HACK: on windows: https://pypi.org/project/windows-curses/
                curses.resize_term(0, 0)
            elif ch == curses.KEY_UP:
                self.cur_page = max(self.cur_page - 1, 0)
            elif ch == curses.KEY_DOWN:
                self.cur_page = min(self.cur_page + 1, max_page)
            elif ch == curses.KEY_LEFT:
                self.caret_pos = max(self.caret_pos - 1, 0)
            elif ch == curses.KEY_RIGHT:
                self.caret_pos = min(self.caret_pos + 1, len(self.cur_input))
            elif ch == ord("\b"):
                self.cur_input = (
                    self.cur_input[: self.caret_pos - 1]
                    + self.cur_input[self.caret_pos :]
                )
                self.caret_pos = max(self.caret_pos - 1, 0)
                text_changed = True
            elif ch == curses.ascii.ctrl(ord("c")):  # Ctrl + C
                if self.select_mode:
                    self.cur_input = self.search_str
                    self.caret_pos = len(self.search_str)
                    self.select_mode = False
                else:
                    self.cur_input = ""
                    self.caret_pos = 0
                    self.select_mode = False
                    text_changed = True
            elif ch == curses.ascii.ctrl(ord("w")):
                self.exit = True
            elif ch == ord("\n"):
                if not self.select_mode:
                    self.select_mode = True
                    self.search_str = self.cur_input
                    self.cur_input = ""
                    self.caret_pos = 0
                elif self.select_mode and self.on_item_selected:
                    self.on_item_selected(int(self.cur_input))
            else:
                self.cur_input = (
                    self.cur_input[: self.caret_pos]
                    + chr(ch)
                    + self.cur_input[self.caret_pos :]
                )
                self.caret_pos += 1
                text_changed = True

            if (
                text_changed
                and not self.select_mode
                and self.on_text_changed is not None
            ):
                self.on_text_changed(self.cur_input)

            if self.block_mode:
                break

    def update(self):
        cur_time = time.time()
        if cur_time > self.last_update + 0.5 or self.block_mode:
            self.last_update = cur_time

            self.update_input(self.stdscr)
            self.update_screen(self.stdscr)

    def exec(self):
        self.set_block_mode(True)
        self.update_screen(self.stdscr)
        while True:
            if self.exit:
                return
            self.update()

    def set_block_mode(self, block_mode):
        self.block_mode = block_mode
        self.stdscr.nodelay(not block_mode)


def activate_cur_terminal():
    if sys.platform == "win32":
        import ctypes

        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        ctypes.windll.user32.SetForegroundWindow(hwnd)


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


class SearchWindow:
    def __init__(self, stdscr, items, label=">", text=""):
        self.input_ = InputWidget(label=label, text=text)
        self.items = items
        self.closed = False
        self.stdscr = stdscr
        self.matched_item_indices = []
        self.selected_index = 0
        self.width = -1
        self.height = -1

        last_input = None
        self.on_main_loop()
        while True:
            self.height, self.width = stdscr.getmaxyx()

            if last_input != self.get_text():
                last_input = self.get_text()

                # Search scripts
                self.matched_item_indices = list(search_items(items, self.get_text()))

                self.selected_index = 0

            # Sreen update
            stdscr.clear()
            self.on_update_screen()
            stdscr.refresh()

            # Keyboard event
            ch = stdscr.getch()

            if ch == -1:  # getch() timeout
                pass

            elif self.on_getch(ch):
                pass

            elif ch == ord("\n"):
                self.on_enter_pressed()

            elif ch == curses.KEY_UP:
                self.selected_index = max(self.selected_index - 1, 0)

            elif ch == curses.KEY_DOWN:
                self.selected_index = min(
                    self.selected_index + 1, len(self.matched_item_indices) - 1
                )

            elif ch == curses.ascii.ESC:
                return

            elif ch != 0:
                self.input_.on_getch(ch)

            if self.closed:
                return

            self.on_main_loop()

    def get_selected_index(self):
        if len(self.matched_item_indices) > 0:
            return self.matched_item_indices[self.selected_index]
        else:
            return -1

    def get_text(self):
        return self.input_.text

    def on_update_screen(self):
        # Get matched scripts
        row = 2
        for i, item_index in enumerate(self.matched_item_indices):
            if self.selected_index == i:  # Hightlight on
                self.stdscr.attron(curses.color_pair(2))
            self.stdscr.addstr(
                row, 0, "%d. %s" % (item_index + 1, str(self.items[item_index]))
            )
            if self.selected_index == i:  # Highlight off
                self.stdscr.attroff(curses.color_pair(2))

            row += 1
            if row >= self.height:
                break

        self.input_.on_update_screen(self.stdscr, 0, cursor=True)

    def get_selected_item(self):
        if len(self.matched_item_indices) > 0:
            item_index = self.matched_item_indices[self.selected_index]
            return self.items[item_index]
        else:
            return None

    def on_getch(self, ch):
        return False

    def on_enter_pressed(self):
        pass

    def on_tab_pressed(self):
        pass

    def on_main_loop(self):
        pass

    def close(self):
        self.closed = True


def init_curses():
    curses.noecho()
    curses.cbreak()
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
    stdscr = curses.initscr()
    stdscr.keypad(1)
    stdscr.nodelay(False)
    stdscr.timeout(1000)
