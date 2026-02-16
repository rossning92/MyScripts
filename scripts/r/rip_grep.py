import argparse
import json
import os
import re
import shlex
import signal
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from threading import Thread
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple

from _script import start_script
from utils.jsonutil import load_json, save_json
from utils.menu import Menu

_MODULE_NAME = Path(__file__).stem
_DEFAULT_CONTEXT = 0


def run_ripgrep(
    pattern: str,
    path: str,
    context: int = 0,
    exclude: Optional[str] = None,
    on_match: Optional[Callable[[str, List[Tuple[bool, int, str]]], None]] = None,
    on_message: Optional[Callable[[str], None]] = None,
    on_process: Optional[Callable[[subprocess.Popen], None]] = None,
):
    args = [
        "rg",
        "--ignore-case",
        "-C",
        str(context),
        "--json",
        "--glob",
        "!*.bak",
    ]
    if exclude:
        args += ["--glob", "!" + exclude]

    # Search pattern
    args.append(pattern)

    # Search file path (if specified)
    if os.path.isfile(path):
        args.append(path)

    if on_message:
        on_message(shlex.join(args))

    process = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        text=True,
        encoding="utf-8",
        cwd=path if os.path.isdir(path) else None,
    )

    if on_process:
        on_process(process)

    # variables
    last_file_path = ""
    last_line_number = 0
    lines: List[Tuple[bool, int, str]] = []

    try:
        while True:
            assert process.stdout
            json_str = process.stdout.readline()
            if not json_str:
                break

            data = json.loads(json_str)
            data_type = data.get("type")
            if data_type in ("context", "match"):
                file_path = data["data"]["path"]["text"]
                data_lines = data["data"]["lines"]
                line_text = data_lines["text"].rstrip()
                line_number = data["data"]["line_number"]

                # A code block is ready
                if last_file_path and (
                    file_path != last_file_path or line_number != last_line_number + 1
                ):
                    if on_match:
                        on_match(last_file_path, lines)
                    lines.clear()

                lines.append(
                    (
                        True if data_type == "match" else False,
                        line_number,
                        line_text,
                    )
                )
                last_file_path = file_path
                last_line_number = line_number

        if last_file_path and lines:
            if on_match:
                on_match(last_file_path, lines)

        assert process.stderr
        stderr_output = process.stderr.read()
        if stderr_output:
            if on_message:
                on_message(f"error: {stderr_output.strip()}")

        process.wait()
        if on_message:
            if process.returncode != 0:
                on_message(f"rg exited with code {process.returncode}")
            else:
                on_message("search completed")

    except Exception as e:
        if on_message:
            on_message(str(e))


@dataclass
class _Match:
    file: str


class _Line:
    def __init__(
        self,
        text: str,
        type: Literal["file", "matched_line", "context_line"],
        match: _Match,
        line_number: Optional[int] = None,
    ) -> None:
        self.text: str = text
        self.type: Literal["file", "matched_line", "context_line"] = type
        self.match: _Match = match
        self.line_number = line_number

    def __str__(self) -> str:
        return self.text


class GrepMenu(Menu[_Line]):
    def __init__(
        self,
        path: Optional[str] = None,
        pattern: Optional[str] = None,
        context=_DEFAULT_CONTEXT,
        exclude: Optional[str] = None,
        **kwargs,
    ):
        self.__context = context
        self.__path = path if path else os.getcwd()
        self.__exclude = exclude
        self.__last_file: Optional[str] = None
        self.__data_file = os.path.join(".config", f"{_MODULE_NAME}.json")
        self.__data: Dict[str, Any] = load_json(self.__data_file, default={})
        self.__pattern = ""
        self.__thread: Optional[Thread] = None
        self.__process: Optional[subprocess.Popen] = None

        super().__init__(
            prompt=f"grep ({self.__path})",
            search_mode=False,
            line_number=False,
            **kwargs,
        )

        self.add_command(self.__list_search_history, hotkey="ctrl+l")
        self.add_command(self.__edit_file, hotkey="ctrl+e")

        if pattern:
            self.set_input(pattern)

    def get_item_text(self, line: _Line) -> str:
        return (
            line.text if line.type == "file" else f"{line.line_number:3d} {line.text}"
        )

    def __list_search_history(self):
        history: List[str] = self.__data["history"]
        i = Menu(items=history).exec()
        if i < 0:
            return

        self.__start_rg(history[i])

    def __edit_file(self):
        selected = self.get_selected_item()
        if selected:
            file_path = selected.match.file
            start_script(
                "ext/vim_edit.py",
                args=[
                    os.path.join(self.__path, file_path),
                    "--line",
                    str(selected.line_number),
                ],
            )

    def __add_match(self, file: str, lines: List[Tuple[bool, int, str]]):
        file_path = file.replace(os.path.sep, "/")
        match = _Match(file=file_path)

        if match.file != self.__last_file:
            self.append_item(_Line(match.file, type="file", match=match))
        elif _DEFAULT_CONTEXT > 0:
            self.append_item(_Line("", type="file", match=match))
        self.__last_file = match.file

        for is_match, line_number, line in lines:
            self.append_item(
                _Line(
                    (
                        re.sub(
                            "(" + self.__pattern + ")",
                            "\x1b[1;31m\\1\x1b[0m",
                            line,
                            flags=re.IGNORECASE,
                        )
                        if is_match
                        else line
                    ),
                    type="matched_line" if is_match else "context_line",
                    match=match,
                    line_number=line_number,
                )
            )

    def get_item_color(self, line: _Line) -> str:
        if line.type == "file":
            return "cyan"
        else:
            return "white"

    def on_enter_pressed(self):
        input_str = self.get_input()
        self.__start_rg(input_str)

    def __start_rg(self, pattern: str):
        self.__stop_rg()

        self.items.clear()
        self.__last_file = None
        self.__pattern = pattern

        # Save search history
        if "history" not in self.__data:
            self.__data["history"] = []
        try:
            self.__data["history"].remove(pattern)
        except ValueError:
            pass
        self.__data["history"].insert(0, pattern)
        save_json(self.__data_file, self.__data)

        def on_match(file, lines):
            self.__add_match(file=file, lines=lines)

        def on_message(message):
            self.set_message(message)

        def on_process(process):
            self.__process = process

        self.__thread = Thread(
            target=run_ripgrep,
            kwargs=dict(
                pattern=pattern,
                path=self.__path,
                context=self.__context,
                exclude=self.__exclude,
                on_match=on_match,
                on_message=on_message,
                on_process=on_process,
            ),
        )
        self.__thread.start()

    def __stop_rg(self):
        if self.__process:
            if sys.platform == "win32":
                os.kill(self.__process.pid, signal.CTRL_C_EVENT)
            else:
                self.__process.send_signal(signal.SIGINT)
            self.__process.wait()
            self.__process = None

    def on_close(self):
        self.__stop_rg()

    def on_keyboard_interrupt(self):
        self.__stop_rg()
        super().on_keyboard_interrupt()

    def on_escape_pressed(self):
        self.__stop_rg()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path", type=str, nargs="?", default=os.environ.get("SEARCH_PATH")
    )
    parser.add_argument("--pattern", type=str, default=None)
    parser.add_argument("--context", type=int, default=_DEFAULT_CONTEXT)
    parser.add_argument("--exclude", type=str, default=None)
    args = parser.parse_args()

    GrepMenu(
        path=args.path,
        pattern=args.pattern,
        context=args.context,
        exclude=args.exclude,
    ).exec()
