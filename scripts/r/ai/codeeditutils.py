import os
import shutil
from dataclasses import dataclass
from io import StringIO
from typing import List, Optional, Set

from utils.menu.confirmmenu import ConfirmMenu


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


def apply_changes(changes: List[Change]) -> List[str]:
    modified_files: Set[str] = set()
    for c in changes:
        # Back up file before changes.
        if os.path.exists(c.file) and c.file not in modified_files:
            backup_file = f"{c.file}.bak"
            shutil.copyfile(c.file, backup_file)
            modified_files.add(c.file)

        # If search block is empty, create a new file
        if not c.search:
            with open(c.file, "w", encoding="utf-8") as f:  # Create a new file
                f.write(c.replace)
        else:
            with open(c.file, "r+", encoding="utf-8") as f:
                content = f.read()
                if c.search not in content:
                    raise ValueError(f"Search string not found in {c.file}")
                updated_content = content.replace(c.search, c.replace)
                f.seek(0)
                f.write(updated_content)
                f.truncate()

    return list(modified_files)


def apply_change_interactive(changes: List[Change]) -> Optional[List[str]]:
    if len(changes) > 0:
        menu = ApplyChangeMenu(changes=changes)
        menu.exec()
        if menu.is_confirmed():
            return apply_changes(changes)
        else:
            return None
    else:
        return None


def revert_changes(files: List[str]) -> None:
    for file in files:
        backup_file = f"{file}.bak"
        if os.path.exists(backup_file):
            shutil.copyfile(backup_file, file)
            os.remove(backup_file)
        else:
            raise FileNotFoundError(f"No backup found for {file}")
