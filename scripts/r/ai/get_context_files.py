import re
from typing import List

from ML.gpt.chat_menu import ChatMenu
from r.tree import tree
from utils.menu.listeditmenu import ListEditMenu


def _get_prompt(task: str):
    return f"""\
List the files that need to be modified for the coding task I provide.
Return only the file list inside ``` and ```. Nothing else.
Each line must be a full file path.
Return "NOT FOUND" if no files are found or need modification.

## Here is my task:
---
{task}
---

## Here are all the files:
---
{tree()}
---
"""


class GetContextFilesMenu(ChatMenu):
    def __init__(self, task: str, **kwargs) -> None:
        super().__init__(prompt="query files", message=_get_prompt(task=task), **kwargs)

        self.files: List[str] = []

    def on_message(self, content: str):
        if "NOT FOUND" in content:
            self.close()
        else:
            match = re.findall(
                r"```.*?\n([\S\s]+?)\n\s*```", content, flags=re.MULTILINE
            )
            files = match[0].splitlines()
            menu = ListEditMenu(prompt="add files to context?", items=files)
            menu.exec()
            if not menu.is_cancelled and files:
                self.files[:] = files

            self.close()
