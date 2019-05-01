import curses
import curses.ascii
import threading
import time
import re
import signal
from _shutil import *


def getch():
    if platform.system() == 'Windows':
        import msvcrt
        return msvcrt.getch().decode()

    else:
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class InputWindow():
    def __init__(self, text_changed=None):
        self.cur_input = ''
        self.caret_pos = 0
        self.text_changed = text_changed
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
            elif ch == ord('\b'):
                self.cur_input = self.cur_input[:self.caret_pos - 1] + self.cur_input[self.caret_pos:]
                self.caret_pos = max(self.caret_pos - 1, 0)
                text_changed = True
            elif ch == curses.ascii.ctrl(ord('c')):
                if len(self.input_stack) > 0:
                    self.cur_input = self.input_stack.pop()
                    self.caret_pos = len(self.cur_input)
                else:
                    self.cur_input = ''
                    self.caret_pos = 0
                    text_changed = True
            elif ch == curses.ascii.ctrl(ord('w')):
                self.exit = True
            elif ch == ord('\n'):
                self.input_stack.append(self.cur_input)
                self.cur_input = ''
                self.caret_pos = 0
            else:
                self.cur_input = self.cur_input[:self.caret_pos] + chr(ch) + self.cur_input[self.caret_pos:]
                self.caret_pos += 1
                text_changed = True

            if text_changed and self.text_changed:
                self.text_changed(self.cur_input)

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
        self.update_screen(self.stdscr)
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
            self.lines.append(l.decode(errors='replace'))
            self.update()

    def update_screen2(self):
        height, width = self.stdscr.getmaxyx()

        filtered_lines = [l for l in self.lines if self.cur_input.lower() in l.lower()]
        n = min(len(filtered_lines), height - 1)
        for i in range(n):
            self.stdscr.addstr(i, 0, filtered_lines[i])


class ListWidget():
    def __init__(self, lines=None, text_changed=None, item_selected=None):
        self.lines = lines
        self.cur_page = 0
        self.cur_input = ''
        self._cond = threading.Condition()
        self.text_changed = text_changed
        self.item_selected = item_selected
        self.last_update = 0
        self.select_mode = False
        self.search_str = ''
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
            line = '%d ' % idx + line
            line = line.replace('\t', '    ')  # replace tab with space
            line = line[:width]

            # Highlight cur_input
            if self.cur_input:
                match = [(m.start(), m.end()) for m in re.finditer(self.cur_input, line)]
            else:
                match = None

            try:  # HACK: ignore exception on addstr
                if match:
                    substr = line[0: match[0][0]]
                    stdscr.addstr(i, 0, substr)

                    for j in range(len(match)):
                        stdscr.attron(curses.color_pair(3))
                        substr = line[match[j][0]: match[j][1]]
                        stdscr.addstr(i, match[j][0], substr)
                        stdscr.attroff(curses.color_pair(3))

                        end_pos = match[j + 1][0] if j < len(match) - 1 else None
                        substr = line[match[j][1]: end_pos]
                        stdscr.addstr(i, match[j][1], substr)
                else:
                    stdscr.addstr(i, 0, line)
            except:
                pass

        # stdscr.attron(curses.color_pair(2))
        status_text = '[%d / %d]' % (self.cur_page, len(self.lines) // (height - 1))
        stdscr.insstr(height - 1, width - len(status_text), status_text)

        stdscr.addstr(height - 1, 0, self.cur_input)
        stdscr.move(height - 1, self.caret_pos)
        # stdscr.attroff(curses.color_pair(2))

        stdscr.refresh()

    def update_input(self, stdscr):
        height, width = stdscr.getmaxyx()
        # resize = curses.is_term_resized(height, width)
        # if resize is True:
        #     height, width = stdscr.getmaxyx()
        #     curses.resize_term(height, width)

        max_page = len(self.lines) // (height - 1)

        while True:
            text_changed = False
            c = stdscr.getch()

            if c == curses.ERR:
                break
            elif c == curses.KEY_UP:
                self.cur_page = max(self.cur_page - 1, 0)
            elif c == curses.KEY_DOWN:
                self.cur_page = min(self.cur_page + 1, max_page)
            elif c == curses.KEY_LEFT:
                self.caret_pos = max(self.caret_pos - 1, 0)
            elif c == curses.KEY_RIGHT:
                self.caret_pos = min(self.caret_pos + 1, len(self.cur_input))
            elif c == ord('\b'):
                self.cur_input = self.cur_input[:self.caret_pos - 1] + self.cur_input[self.caret_pos:]
                self.caret_pos = max(self.caret_pos - 1, 0)
                text_changed = True
            elif c == 0x7F:  # Ctrl + Backspace
                if self.select_mode:
                    self.cur_input = self.search_str
                    self.caret_pos = len(self.search_str)
                    self.select_mode = False
                else:
                    self.cur_input = ''
                    self.caret_pos = 0
                    self.select_mode = False
                    text_changed = True
            elif c == curses.ascii.ctrl(ord('c')):
                self.exit = True
            elif c == ord('\n'):
                if not self.select_mode:
                    self.select_mode = True
                    self.search_str = self.cur_input
                    self.cur_input = ''
                    self.caret_pos = 0
                elif self.select_mode and self.item_selected:
                    self.item_selected(int(self.cur_input))
            else:
                self.cur_input = self.cur_input[:self.caret_pos] + chr(c) + self.cur_input[self.caret_pos:]
                self.caret_pos += 1
                text_changed = True

            if text_changed and not self.select_mode:
                self.text_changed(self.cur_input)

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


def wait_key(prompt=None, timeout=2):
    if prompt is None:
        prompt = 'Press enter to skip...'

    def main(stdscr):
        stdscr.nodelay(True)
        stdscr.addstr(prompt)
        elapsed = 0.0
        while True:
            if elapsed > timeout:
                return False

            stdscr.addstr(0, 0, '%s (%d)' % (prompt, int(timeout - elapsed) + 1))

            ch = stdscr.getch()
            if ch == ord('\n'):
                return True

            time.sleep(0.1)
            elapsed += 0.1

    return curses.wrapper(main)
