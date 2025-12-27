import subprocess
import sys

from utils.process import start_process

from .textmenu import TextMenu


class DiffMenu(TextMenu):
    def __init__(self, file1: str, file2: str, **kwargs):
        self.file1 = file1
        self.file2 = file2

        cp = subprocess.run(
            [
                "git",
                "diff",
                "--color",
                "--ignore-space-change",
                "--color-moved=dimmed-zebra",
                "--color-moved-ws=allow-indentation-change",
                "--no-index",
                file1,
                file2,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        super().__init__(
            prompt=f"diff: {file1} <=> {file2}",
            text=cp.stdout,
            wrap_text=False,
            **kwargs,
        )
        self.add_command(self.__open_in_vscode, hotkey="ctrl+o")

    def __open_in_vscode(self):
        start_process(
            [
                (
                    r"C:\Program Files\Microsoft VS Code\bin\code.cmd"
                    if sys.platform == "win32"
                    else "code"
                ),
                "--diff",
                self.file1,
                self.file2,
            ]
        )
