from dataclasses import dataclass
from io import StringIO
from typing import Any, List, Optional, Set, Tuple

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
    def __init__(self, changes: List[Change], **kwargs) -> None:
        super().__init__(
            prompt=f"apply changes ({len(changes)})?",
            items=self.format_changes(changes).splitlines(),
            wrap_text=True,
            **kwargs,
        )

    def format_changes(self, changes: List[Change]) -> str:
        return "\n".join(str(c) for c in changes)

    def get_item_color(self, item: str) -> str:
        if item.startswith("+ "):
            return "green"
        elif item.startswith("- "):
            return "red"
        else:
            return "white"


def apply_changes(
    changes: List[Change], file_list: Optional[List[Any]] = None
) -> List[str]:
    modified_files: Set[str] = set()
    for c in changes:
        # If search block is empty, create a new file
        if not c.search:
            with open(c.file, "w", encoding="utf-8") as f:  # Create a new file
                f.write(c.replace)
        else:
            with open(c.file, "r", encoding="utf-8") as f:
                content = f.read()
                if "\r\n" in content:
                    newline = "\r\n"
                else:
                    newline = "\n"

            if file_list:
                # Find corresponding code blocks in context
                code_blocks = [
                    block for block in file_list if c.search in block["content"]
                ]
                if not code_blocks:
                    raise ValueError(
                        f'Cannot find any match in "{c.file}":\n```\n{c.search}\n```'
                    )
                code_block = code_blocks[0]

                # Replace
                content = replace_text_in_line_range(
                    c.search,
                    c.replace,
                    content=content,
                    start=code_block["line_start"],
                    end=code_block["line_end"],
                )
            else:
                count = content.count(c.search)
                if count == 0:
                    raise ValueError(
                        f'Cannot find any match in "{c.file}":\n```\n{c.search}\n```'
                    )
                elif count > 1:
                    raise ValueError(
                        f'Found more than one match in "{c.file}". '
                        "You can try adding some surrounding lines in order to uniquely match the search block:\n"
                        f"```\n{c.search}\n```"
                    )
                content = content.replace(c.search, c.replace)

            # Save file
            with open(c.file, "w", encoding="utf-8", newline=newline) as f:
                f.write(content)

    return list(modified_files)


def apply_change_interactive(
    changes: List[Change], file_list: Optional[List[Any]] = None
) -> Optional[List[str]]:
    if len(changes) > 0:
        menu = ApplyChangeMenu(changes=changes)
        menu.exec()
        if menu.is_confirmed():
            return apply_changes(changes=changes, file_list=file_list)
        else:
            return None
    else:
        return None
