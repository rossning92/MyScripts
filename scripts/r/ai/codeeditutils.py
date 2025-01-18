import os
import shutil
from dataclasses import dataclass
from typing import List, Set

from utils.menu.confirmmenu import ConfirmMenu


@dataclass
class Change:
    file: str
    search: str
    replace: str


class ApplyChangeMenu(ConfirmMenu):
    def __init__(self, items: List[Change], **kwargs) -> None:
        super().__init__(
            prompt=f"apply changes ({len(items)})?",
            items=items,
            wrap_text=True,
            **kwargs,
        )

    def get_item_text(self, c: Change) -> str:
        search = c.search + "\n" if c.search else ""
        replace = c.replace + "\n" if c.replace else ""
        return (
            f"{c.file}\n"
            "```\n"
            "<<<<<<< SEARCH\n"
            f"{search}"
            "=======\n"
            f"{replace}"
            ">>>>>>> REPLACE\n"
            "```"
        )


def apply_changes(changes: List[Change]) -> List[str]:
    modified_files: Set[str] = set()
    for c in changes:
        # Back up file before changes.
        if c.file not in modified_files:
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


def apply_change_interactive(changes: List[Change]) -> List[str]:
    if len(changes) > 0:
        menu = ApplyChangeMenu(items=changes)
        menu.exec()
        if menu.is_confirmed():
            return apply_changes(changes)
        else:
            return []
    else:
        return []


def revert_changes(files: List[str]) -> None:
    for file in files:
        backup_file = f"{file}.bak"
        if os.path.exists(backup_file):
            shutil.copyfile(backup_file, file)
            os.remove(backup_file)
        else:
            raise FileNotFoundError(f"No backup found for {file}")
