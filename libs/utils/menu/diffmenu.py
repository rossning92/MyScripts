import os
import re
import subprocess
from typing import List, Optional, Tuple, Union

from _script import start_script

from utils.git import get_git_root

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


def _run_git_diff(args: List[str]) -> List[str]:
    cmd = [
        "git",
        "diff",
        "--color",
        "--ignore-space-change",
        "--color-moved=zebra",
        "--color-moved-ws=allow-indentation-change",
    ] + args
    cp = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    lines = []
    for line in cp.stdout.splitlines():
        stripped = _strip_ansi(line)
        if stripped.startswith(("diff --git", "index ")):
            continue
        lines.append(line)
    return lines


class DiffMenu(TextMenu):
    def __init__(self, files: Optional[List[Tuple[str, str]]] = None, **kwargs):
        self.__git_root = None
        lines = []

        if files:
            for f1, f2 in files:
                lines.extend(_run_git_diff(["--no-index", f1, f2]))
        else:
            git_root = get_git_root()
            if git_root:
                self.__git_root = str(git_root)

            args = []
            if subprocess.run(["git", "diff", "--quiet"]).returncode == 0:
                args.extend(["HEAD~1", "HEAD"])

            lines = _run_git_diff(args)

        self.__diff_lines = [_strip_ansi(line) for line in lines]

        super().__init__(
            prompt="diff",
            text="\n".join(lines),
            wrap_text=False,
            **kwargs,
        )

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

    def get_item_color(self, item: str) -> Union[str, Tuple[str, str]]:
        stripped_item = _strip_ansi(item)
        if stripped_item.startswith("---") or stripped_item.startswith("+++"):
            return ("black", "yellow")
        return super().get_item_color(item)

    def on_enter_pressed(self):
        self.__edit_file()
