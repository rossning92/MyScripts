import curses
import curses.ascii
import threading
import time
import re
import signal


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

        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(1)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_YELLOW)
        self.stdscr.nodelay(True)

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

        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(height - 1, 0, '(%d / %d)' % (self.cur_page, len(self.lines) // (height - 1)) + self.cur_input)
        stdscr.attroff(curses.color_pair(2))

        stdscr.refresh()

    def update_input(self, stdscr):
        height, width = stdscr.getmaxyx()
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
            elif c == curses.KEY_BACKSPACE or c == 127 or c == ord('\b'):
                self.cur_input = self.cur_input[:-1]
                text_changed = True
            elif c == curses.ascii.ctrl(ord('c')):
                if self.select_mode:
                    self.cur_input = self.search_str
                    self.select_mode = False
                else:
                    self.cur_input = ''
                    self.select_mode = False
                    text_changed = True
            elif c == ord('\n'):
                if not self.select_mode:
                    self.select_mode = True
                    self.search_str = self.cur_input
                    self.cur_input = ''
                elif self.select_mode and self.item_selected:
                    self.item_selected(int(self.cur_input))
            else:
                self.cur_input += chr(c)
                text_changed = True

            if text_changed and not self.select_mode:
                self.text_changed(self.cur_input)

    def update(self):
        cur_time = time.time()
        if cur_time > self.last_update + 0.5:
            self.last_update = cur_time

            self.update_input(self.stdscr)
            self.update_screen(self.stdscr)


def sigint_handler(signum, frame):
    pass


signal.signal(signal.SIGINT, sigint_handler)
