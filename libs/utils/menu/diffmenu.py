import os
import re
import subprocess
import sys
from typing import List, Optional, Tuple, Union

from _script import start_script

from utils.git import get_git_root
from utils.process import start_process

from .textmenu import TextMenu


def _strip_ansi(s: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def _get_diff_line_info(diff_lines: List[str], index: int) -> Optional[Tuple[str, int]]:
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
            return filename, current_line
    return None


class DiffMenu(TextMenu):
    def __init__(
        self, file1: Optional[str] = None, file2: Optional[str] = None, **kwargs
    ):
        self.__file1 = file1
        self.__file2 = file2
        self.__git_root = None

        cmd = [
            "git",
            "diff",
            "--color",
            "--ignore-space-change",
            "--color-moved=zebra",
            "--color-moved-ws=allow-indentation-change",
        ]
        if self.__file1 and self.__file2:
            cmd.extend(["--no-index", self.__file1, self.__file2])
        else:
            git_root = get_git_root()
            if git_root:
                self.__git_root = str(git_root)

            if subprocess.run(["git", "diff", "--quiet"]).returncode == 0:
                cmd.extend(["HEAD~1", "HEAD"])

        cp = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        raw_lines = cp.stdout.splitlines()
        filtered_lines = []
        for line in raw_lines:
            stripped = _strip_ansi(line)
            if stripped.startswith(
                (
                    "diff --git",
                    "index ",
                )
            ):
                continue
            filtered_lines.append(line)

        self.__diff_lines = [_strip_ansi(line) for line in filtered_lines]

        super().__init__(
            prompt="diff",
            text="\n".join(filtered_lines),
            wrap_text=False,
            **kwargs,
        )

        self.add_command(self.__open_in_vscode, hotkey="ctrl+o")
        self.add_command(self.__edit_file, hotkey="ctrl+e")

    def __edit_file(self):
        index = self.get_selected_index()
        if index < 0 or index >= len(self.__diff_lines):
            return
        info = _get_diff_line_info(self.__diff_lines, index)
        if info:
            filename, line_number = info
            if self.__git_root and not os.path.isabs(filename):
                filename = os.path.join(self.__git_root, filename)

            start_script(
                "ext/edit.py",
                args=[os.path.abspath(filename), "--line", str(line_number)],
            )

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

    def get_item_color(self, item: str) -> Union[str, Tuple[str, str]]:
        stripped_item = _strip_ansi(item)
        if stripped_item.startswith("---") or stripped_item.startswith("+++"):
            return ("black", "yellow")
        return super().get_item_color(item)

    def on_enter_pressed(self):
        self.__edit_file()
