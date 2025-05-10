import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple

from _shutil import send_ctrl_c, write_temp_file
from utils.menu import Menu
from utils.menu.inputmenu import InputMenu


@dataclass
class _Match:
    file: str
    content: str
    line_start: int
    line_end: int
    lines: List[Tuple[bool, int, str]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(asdict(self))


class _Line:
    def __init__(
        self,
        text: str,
        type: Literal["file", "matched", "context"],
        match: _Match,
    ) -> None:
        self.text: str = text
        self.type: Literal["file", "matched", "context"] = type
        self.match: _Match = match

    def __str__(self) -> str:
        return self.text

    def get_color(self):
        if self.type == "file":
            return "yellow"
        elif self.type == "matched":
            return "green"
        else:
            return "white"


class GrepMenu(Menu[_Line]):
    def __init__(
        self,
        search_dir: Optional[str] = None,
        query: Optional[str] = None,
        context=3,
        exclude: Optional[str] = None,
        **kwargs,
    ):
        self.__context = context
        self.__search_dir = search_dir if search_dir else os.getcwd()
        self.__matches: List[_Match] = []
        self.__exclude = exclude

        super().__init__(
            prompt=f"grep ({self.__search_dir})",
            search_mode=False,
            line_number=False,
            **kwargs,
        )

        self.add_command(self.__delete_selected, hotkey="ctrl+k")
        self.add_command(self.__run_coder, hotkey="ctrl+t")
        self.add_command(self.__save_matches, hotkey="ctrl+s")
        self.add_command(self.__show_less, hotkey="alt+l")
        self.add_command(self.__show_more, hotkey="alt+m")

        if query:
            self.set_input(query)

    def __show_less(self):
        self.__update_items(show_code=False)

    def __show_more(self):
        self.__update_items(show_code=True)

    def __run_coder(self):
        m = InputMenu(prompt="task")
        task = m.request_input()
        if task:
            for i, match in enumerate(self.get_selected_items()):
                self.set_message(f"processing match {i+1}")
                tmpfile = write_temp_file("[" + match.match.to_json() + "]", ".json")
                ret_code = self.call_func_without_curses(
                    lambda tmpfile=tmpfile: subprocess.call(
                        [
                            "run_script",
                            "@command_wrapper=1",
                            "r/ai/coder.py",
                            "--yes",
                            "--task",
                            task,
                            "--context",
                            tmpfile,
                        ]
                    )
                )
                self.set_message(f"done with {i+1}")
                if ret_code != 0:
                    break

    def __save_matches(self):
        data = [match.to_dict() for match in self.__matches]
        with open("matches.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self.set_message("matches saved to matches.json")

    def __delete_selected(self):
        selected = self.get_selected_item()
        if selected:
            self.__matches.remove(selected.match)
        self.__update_items(True)

    def __add_match(self, file: str, lines: List[Tuple[bool, int, str]]):
        file_path = file.replace(os.path.sep, "/")
        content = file_path + "\n"
        line_start = sys.maxsize
        line_end = 0
        for is_match, line_number, line in lines:
            line_start = min(line_number, line_start)
            line_end = max(line_number, line_end)
            content += line
        match = _Match(
            file=file_path,
            content=content,
            line_start=line_start,
            line_end=line_end,
            lines=lines.copy(),
        )
        self.__matches.append(match)

        self.__update_items(show_code=True)

    def __update_items(self, show_code: bool):
        self.clear_items()
        for match in self.__matches:
            self.append_item(_Line(match.file, type="file", match=match))
            if show_code:
                for is_match, line_number, line in match.lines:
                    self.append_item(
                        _Line(
                            f"{line_number:3d} {line}",
                            type="matched" if is_match else "context",
                            match=match,
                        )
                    )

    def get_item_color(self, item: _Line) -> str:
        return item.get_color()

    def on_enter_pressed(self):
        self.items.clear()
        input_str = self.get_input()
        args = [
            "rg",
            "--ignore-case",
            "-C",
            str(self.__context),
            "--json",
            "--glob",
            "!*.bak",
        ]
        if self.__exclude:
            args += ["--glob", "!" + self.__exclude]
        args.append(input_str)

        self.set_message(f"{args}")
        self.process_events()

        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            text=True,
            encoding="utf-8",
            cwd=self.__search_dir if self.__search_dir else None,
        )

        # variables
        last_file_path = ""
        last_line_number = 0
        lines: List[Tuple[bool, int, str]] = []
        self.__matches.clear()

        while True:
            assert process.stdout
            json_str = process.stdout.readline()
            if not json_str:
                break

            data = json.loads(json_str)
            data_type = data["type"]
            if data_type in ("context", "match"):
                file_path = data["data"]["path"]["text"]
                data_lines = data["data"]["lines"]
                line_text = data_lines["text"]
                line_number = data["data"]["line_number"]

                # A code block is ready
                if last_file_path and (
                    file_path != last_file_path or line_number != last_line_number + 1
                ):
                    self.__add_match(file=last_file_path, lines=lines)

                    lines.clear()

                lines.append(
                    (True if data_type == "match" else False, line_number, line_text)
                )
                last_file_path = file_path
                last_line_number = line_number
            try:
                self.process_events(raise_keyboard_interrupt=True)
            except KeyboardInterrupt:
                send_ctrl_c(process)
                break

        if last_file_path and lines:
            self.__add_match(file=last_file_path, lines=lines)

        assert process.stderr
        stderr_output = process.stderr.read()
        if stderr_output:
            self.set_message(f"error: {stderr_output.strip()}")

        process.wait()
        if process.returncode != 0:
            self.set_message("process exited with code {process.returncode}")
        else:
            self.set_message("search completed")

        self.update_screen()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("search_dir", type=str, nargs="?")
    parser.add_argument("--query", type=str, default=None)
    parser.add_argument("--context", type=int, default=3)
    parser.add_argument("--exclude", type=str, default=None)
    args = parser.parse_args()

    GrepMenu(
        search_dir=args.search_dir,
        query=args.query,
        context=args.context,
        exclude=args.exclude,
    ).exec()
