import glob
import os
import time
from typing import Iterable, Iterator, List, Optional

from _editor import open_code_editor
from _script import get_relative_script_path
from utils.menu import Menu
from utils.menu.textinput import TextInput


class _MatchedLine:
    def __init__(
        self, relative_path: str, full_path: str, line_no: int, line: str
    ) -> None:
        self.relative_path = relative_path
        self.full_path = full_path
        self.line_no = line_no
        self.line = line

    def __str__(self) -> str:
        return f"{self.relative_path}:{self.line_no}:{self.line}"


def _find_matched_lines(
    s: str,
    files: Iterable[str],
) -> Iterator[_MatchedLine]:
    for i, file in enumerate(files):
        try:
            with open(file, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()

            for i, line in enumerate(lines):
                if s in line:
                    yield _MatchedLine(
                        relative_path=get_relative_script_path(file),
                        full_path=file,
                        line_no=i + 1,
                        line=lines[i],
                    )

        except UnicodeDecodeError:
            pass


class _FindResultMenu(Menu[_MatchedLine]):
    def __init__(
        self,
        keyword: str,
        files: Iterable[str],
    ):
        self.__find_result: List[_MatchedLine] = []
        self.__keyword = keyword
        self.__files = files
        super().__init__(prompt="Result:", items=self.__find_result)

    def on_created(self):
        last_time = 0.0

        for line in _find_matched_lines(self.__keyword, files=self.__files):
            now = time.time()
            self.__find_result.append(line)
            if now - last_time > 0.1:
                last_time = now
                self.process_events()
                self.set_message("searching...")

        self.set_message(None)


def find_in_files(files: Iterable[str], history_file: Optional[str] = None):
    text_input = TextInput(history_file=history_file)
    keyword = text_input.request_input()

    if keyword:
        find_result_menu = _FindResultMenu(keyword, files=files)
        find_result_menu.exec()
        selected_line = find_result_menu.get_selected_item()
        if selected_line is not None:
            open_code_editor(selected_line.full_path, line_number=selected_line.line_no)


if __name__ == "__main__":
    find_in_files(
        files=(
            file
            for file in glob.glob(os.path.join(os.getcwd(), "**", "*"), recursive=True)
            if os.path.isfile(file)
        )
    )
