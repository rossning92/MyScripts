import re
import subprocess
import sys
from typing import List, Optional

from utils.editor import open_code_editor
from utils.process import start_process

from .textmenu import TextMenu


def _strip_ansi(s: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def _open_diff_line(diff_lines: List[str], index: int):
    filename = None
    new_line_start = None
    chunk_header_index = -1

    for i in range(index, -1, -1):
        line = diff_lines[i]
        if line.startswith("@@ "):
            match = re.search(r"\+(\d+)", line)
            if match:
                new_line_start = int(match.group(1))
                chunk_header_index = i
                break

    if new_line_start is not None:
        for i in range(chunk_header_index, -1, -1):
            line = diff_lines[i]
            if line.startswith("+++ b/"):
                filename = line[6:]
                break
            elif line.startswith("+++ "):
                filename = line[4:]
                if filename == "/dev/null":
                    filename = None
                break

        if filename:
            current_line = new_line_start
            for i in range(chunk_header_index + 1, index):
                line = diff_lines[i]
                if not line.startswith("-"):
                    current_line += 1

            open_code_editor(filename, line_number=current_line)


class DiffMenu(TextMenu):
    def __init__(
        self, file1: Optional[str] = None, file2: Optional[str] = None, **kwargs
    ):
        self.__file1 = file1
        self.__file2 = file2

        cmd = [
            "git",
            "diff",
            "--color",
            "--ignore-space-change",
            "--color-moved=dimmed-zebra",
            "--color-moved-ws=allow-indentation-change",
        ]
        if self.__file1 and self.__file2:
            cmd.extend(["--no-index", self.__file1, self.__file2])
        else:
            if subprocess.run(["git", "diff", "--quiet"]).returncode == 0:
                cmd.extend(["HEAD~1", "HEAD"])

        cp = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.__diff_lines = [_strip_ansi(line) for line in cp.stdout.splitlines()]

        super().__init__(
            prompt="diff",
            text=cp.stdout,
            wrap_text=False,
            **kwargs,
        )

        self.add_command(self.__open_in_vscode, hotkey="ctrl+o")

    def __open_in_vscode(self):
        if self.__file1 and self.__file2:
            start_process(
                [
                    (
                        r"C:\Program Files\Microsoft VS Code\bin\code.cmd"
                        if sys.platform == "win32"
                        else "code"
                    ),
                    "--diff",
                    self.__file1,
                    self.__file2,
                ]
            )

    def on_enter_pressed(self):
        index = self.get_selected_index()
        if index < 0 or index >= len(self.__diff_lines):
            return
        _open_diff_line(self.__diff_lines, index)
