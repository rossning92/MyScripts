import json
import subprocess
from typing import List, Literal, Tuple

from _shutil import send_ctrl_c
from utils.menu import Menu


class _Line:
    def __init__(self, text: str, type: Literal["file", "matched", "context"]) -> None:
        self.text: str = text
        self.type: Literal["file", "matched", "context"] = type

    def __str__(self) -> str:
        return self.text

    def get_color(self):
        if self.type == "file":
            return "CYAN"
        elif self.type == "matched":
            return "green"
        else:
            return "white"


class GrepMenu(Menu[_Line]):
    def __init__(self, **kwargs):
        super().__init__(search_mode=False, **kwargs)

    def __add_match(self, file: str, lines: List[Tuple[bool, str]]):
        self.append_item(_Line(file, type="file"))
        for is_match, line in lines:
            self.append_item(_Line(line, type="matched" if is_match else "context"))

    def get_item_color(self, item: _Line) -> str:
        return item.get_color()

    def on_enter_pressed(self):
        self.items.clear()
        input_str = self.get_input()
        args = ["rg", "-C", "3", "--json", input_str]
        process = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, text=True
        )

        # variables
        last_file_path = ""
        last_line_number = 0
        lines: List[Tuple[bool, str]] = []
        search_result_count = 0

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
                    self.__add_match(file=file_path, lines=lines)

                    lines.clear()
                    search_result_count += 1

                lines.append((True if data_type == "match" else False, line_text))
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
            self.set_message(f"Error: {stderr_output.strip()}")

        process.wait()
        if process.returncode != 0:
            self.set_message(f"Process exited with code {process.returncode}")

        self.update_screen()


if __name__ == "__main__":
    GrepMenu().exec()
