import os
from io import StringIO
from typing import Any, List, Optional

from ai.codeeditutils import read_file_from_line_range, read_file_lines
from utils.menu.filemenu import FileMenu
from utils.menu.listeditmenu import ListEditMenu


class FileContextMenu(ListEditMenu):
    def __init__(
        self,
        items: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
        file_list_json: Optional[str] = None,
    ):
        super().__init__(
            items=items,
            json_file=file_list_json,
            prompt="file list",
            wrap_text=True,
        )

        if files:
            self.clear()
            for file in files:
                self.add_file(file)

    def get_item_text(self, item: Any) -> str:
        return "{}#{}-{}".format(item["file"], item["line_start"], item["line_end"])

    def _add_file(self):
        menu = FileMenu(prompt="add file", goto=os.getcwd())
        file = menu.select_file()
        if file is not None:
            self.add_file(file)

    def add_file(self, file: str):
        file_and_lines = file.split("#")

        file = file_and_lines[0]
        if not os.path.isfile(file):
            raise FileNotFoundError(f'"{file}" does not exist')

        if len(file_and_lines) == 2:
            start, end = map(int, file_and_lines[1].split("-"))
            content = read_file_from_line_range(file, start, end)
        else:
            content, lines = read_file_lines(file)
            start, end = 1, len(lines)
        self.append_item(
            {
                "file": file,
                "content": content,
                "line_start": start,
                "line_end": end,
            }
        )

    def get_prompt(self) -> str:
        result = []
        for item in self.items:
            file = item["file"]
            content = item["content"]
            result.append(f"{file}\n```\n{content}\n```")
        return "## Source Code\n" + "\n".join(result)

    def get_summary(self) -> str:
        s = StringIO()
        files = [
            "{}#{}-{}".format(file["file"], file["line_start"], file["line_end"])
            for file in self.items
        ]
        s.write(f"files={files}")
        return s.getvalue()
