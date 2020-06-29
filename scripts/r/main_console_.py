import sys
import os

sys.path.append(os.path.realpath("../../libs"))
sys.path.append(os.path.realpath("../../bin"))

import run_python
import re

from _script import *

# from prompt_toolkit import prompt
# from prompt_toolkit.completion import (
#     WordCompleter,
#     FuzzyWordCompleter,
#     FuzzyCompleter,
#     Completer,
#     Completion,
# )


# while True:
#     text = prompt(
#         "> ",
#         completer=FuzzyWordCompleter([x.name for x in scripts],),
#         complete_while_typing=True,
#     )
#     found = list(filter(lambda x: x.name == text, scripts))
#     if found:
#         list(found)[0].execute()
#     else:
#         print2("ERROR: unrecognized command.", color="red")


import curses
import curses.ascii


class Input:
    def __init__(self):
        self.text = ""
        self.caret_pos = 0

    def on_update_screen(self, stdscr, row, cursor=False):
        

        stdscr.addstr(row, 0, self.text)

        if cursor:
            stdscr.move(row, self.caret_pos)

    def on_getch(self, ch):
        text_changed = False

        if ch == curses.ERR:
            pass
        elif ch == curses.KEY_LEFT:
            self.caret_pos = max(self.caret_pos - 1, 0)
        elif ch == curses.KEY_RIGHT:
            self.caret_pos = min(self.caret_pos + 1, len(self.text))
        elif ch == ord("\b"):
            self.text = self.text[: self.caret_pos - 1] + self.text[self.caret_pos :]
            self.caret_pos = max(self.caret_pos - 1, 0)
            text_changed = True
        elif ch == ord("\n"):
            pass
        elif re.match("[\x00-\x7F]", chr(ch)):
            self.text = (
                self.text[: self.caret_pos] + chr(ch) + self.text[self.caret_pos :]
            )
            self.caret_pos += 1
            text_changed = True

        if text_changed:
            pass


def main(stdscr):
    scripts = []
    modified_time = {}
    load_scripts(scripts, modified_time, autorun=False)

    # # Clear screen
    # stdscr.clear()

    curses.noecho()
    curses.cbreak()
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    stdscr = curses.initscr()
    stdscr.keypad(1)
    stdscr.nodelay(False)

    input_ = Input()

    while True:
        height, width = stdscr.getmaxyx()

        ch = stdscr.getch()
        input_.on_getch(ch)

        # update screen
        stdscr.clear()

        input_.on_update_screen(stdscr, 0)

        row = 2
        for script in filter(lambda x: input_.text in x.name, scripts):
            stdscr.addstr(row, 0, script.name)
            row += 1
            if row >= height:
                break

        stdscr.refresh()


curses.wrapper(main)
