import argparse
import os
import subprocess
import sys
from typing import Optional

from utils.menu import Menu

log_filters = os.path.join(os.environ["MY_DATA_DIR"], "log_filters")


def read_log_filter_file(name):
    with open(os.path.join(log_filters, f"{name}.txt"), "r", encoding="utf-8") as f:
        return f.read()


def view_log(file: str, log_filter: Optional[str] = None):
    with open(file, "r", encoding="utf-8") as f:
        script_dir = os.path.dirname(os.path.abspath(__file__))

        if not log_filter:
            input_fd = f
        else:
            grep_process = subprocess.Popen(
                ["grep", "-E", log_filter],
                stdin=f,
                stdout=subprocess.PIPE,
            )
            input_fd = grep_process.stdout

        highlight_process = subprocess.Popen(
            [
                sys.executable,
                os.path.join(script_dir, "highlight.py"),
                "-p",
                "^.*? D .*=gray",
                "^.*? W .*=yellow",
                "^.*? (E|F) .*=red",
            ],
            stdin=input_fd,
            stdout=subprocess.PIPE,
        )
        less_process = subprocess.Popen(
            ["less", "-iNSR"], stdin=highlight_process.stdout
        )
        less_process.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", default=None, type=str)
    args = parser.parse_args()

    menu = Menu(
        items=[
            os.path.splitext(f)[0]
            for f in os.listdir(log_filters)
            if f.endswith(".txt")
        ]
        if os.path.isdir(log_filters)
        else [],
        prompt="regex>",
        on_item_selected=lambda log_filter_name: view_log(
            file=args.file, log_filter=read_log_filter_file(log_filter_name)
        ),
        close_on_selection=False,
        cancellable=False,
    )
    menu.add_hotkey(
        "ctrl+a",
        lambda: menu.call_func_without_curses(lambda: view_log(file=args.file)),
    )
    menu.exec()
