from dataclasses import dataclass
from io import StringIO
from typing import List, Tuple

from utils.menu.confirmmenu import ConfirmMenu


def read_file_lines(file: str) -> Tuple[str, List[str]]:
    with open(file, "r", encoding="utf-8") as f:
        s = f.read()
        lines = s.splitlines()
    return s, lines


def read_file_from_line_range(file: str, start: int, end: int) -> str:
    _, lines = read_file_lines(file)
    start, end = max(1, start), min(end, len(lines))
    content = "\n".join(lines[start - 1 : end])
    return content


def replace_text_in_line_range(
    search: str, replace: str, content: str, start: int, end: int
) -> str:
    lines = content.split("\n")
    start, end = max(1, start), min(end, len(lines))
    target_region = "\n".join(lines[start - 1 : end])
    updated_region = target_region.replace(search.rstrip(), replace)
    updated_lines = lines[: start - 1] + updated_region.split("\n") + lines[end:]
    updated_content = "\n".join(updated_lines)
    return updated_content


@dataclass
class Change:
    file: str
    search: str
    replace: str

    def __str__(self) -> str:
        output = StringIO()
        output.write(f"{self.file}:\n")
        for line in self.search.splitlines():
            output.write(f"- {line}\n")
        for line in self.replace.splitlines():
            output.write(f"+ {line}\n")
        return output.getvalue()


class ApplyChangeMenu(ConfirmMenu):
    def __init__(self, change: Change, **kwargs) -> None:
        super().__init__(
            prompt="apply change?",
            items=str(change).splitlines(),
            wrap_text=True,
            **kwargs,
        )

    def get_item_color(self, item: str) -> str:
        if item.startswith("+ "):
            return "green"
        elif item.startswith("- "):
            return "red"
        else:
            return "white"


def apply_change(change: Change):
    # If search block is empty, create a new file
    if not change.search:
        with open(change.file, "w", encoding="utf-8") as f:  # Create a new file
            f.write(change.replace)
    else:
        with open(change.file, "r", encoding="utf-8") as f:
            content = f.read()
            if "\r\n" in content:
                newline = "\r\n"
            else:
                newline = "\n"

        count = content.count(change.search)
        if count == 0:
            raise ValueError(
                f'Cannot find any match in "{change.file}":\n```\n{change.search}\n```'
            )
        elif count > 1:
            raise ValueError(
                f'Found more than one match in "{change.file}". '
                "Try adding some surrounding lines in order to uniquely match the search block:\n"
                f"```\n{change.search}\n```"
            )
        content = content.replace(change.search, change.replace)

        # Save file
        with open(change.file, "w", encoding="utf-8", newline=newline) as f:
            f.write(content)


def apply_change_interactive(change: Change) -> bool:
    menu = ApplyChangeMenu(change=change)
    menu.exec()
    if menu.is_confirmed():
        apply_change(change=change)
        return True
    else:
        return False
