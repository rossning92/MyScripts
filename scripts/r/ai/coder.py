import argparse
import os
import re
from typing import Any, List, Optional, Tuple

from ML.gpt.chatmenu import ChatMenu
from r.tree import tree
from utils.menu.confirmmenu import ConfirmMenu
from utils.menu.filemenu import FileMenu
from utils.menu.listeditmenu import ListEditMenu
from utils.menu.textmenu import TextMenu

setting_dir = ".coder"


def get_context_files(task: str):
    return f"""\
List the files that need to be modified for the coding task I provide.
Return only the file list inside ```files and ```. Nothing else.
Each line should be a full file path.
Return empty if no files need modification.

## Here is my task:
---
{task}
---

## Here are all the files:
---
{tree()}
---
"""


def get_coding_prompt(task: str, file_list: str):
    return (
        """\
Act as an expert software developer.
Take requests for changes to the supplied code.
Output a copy of each file that needs changes


Describe each change with a *SEARCH/REPLACE block*
All changes to files must use this *SEARCH/REPLACE block* format.
ONLY EVER RETURN CODE IN A *SEARCH/REPLACE BLOCK*!
Every *SEARCH/REPLACE block* must use this format:

filename.py
```
<<<<<<< SEARCH
...
=======
...
>>>>>>> REPLACE
```

If user specified the file path, then use the exact file path.

Every *SEARCH* section must *EXACTLY MATCH* the existing file content, character for character, including all comments, docstrings, etc.
If the file contains code or other data wrapped/escaped in json/xml/quotes or other containers, you need to propose edits to the literal contents of the file, including the container markup.

*SEARCH/REPLACE* blocks will *only* replace the first match occurrence.
Including multiple unique *SEARCH/REPLACE* blocks if needed.
Include enough lines in each SEARCH section to uniquely match each set of lines that need to change.

Keep *SEARCH/REPLACE* blocks concise.
Break large *SEARCH/REPLACE* blocks into a series of smaller blocks that each change a small portion of the file.
Include just the changing lines, and a few surrounding lines if needed for uniqueness.
Do not include long runs of unchanging lines in *SEARCH/REPLACE* blocks.

Only create *SEARCH/REPLACE* blocks for files that the user has added to the chat!

To move code within a file, use 2 *SEARCH/REPLACE* blocks: 1 to delete it from its current location, 1 to insert it in the new location.

Pay attention to which filenames the user wants you to edit, especially if they are asking you to create a new file.

If you want to put code in a new file, use a *SEARCH/REPLACE block* with:
- A new file path, including dir name if needed
- An empty `SEARCH` section
- The new file's contents in the `REPLACE` section

## My task

"""
        + task
        + (
            "\n\nHere starts the code to be modified:\n\n" + file_list
            if file_list
            else ""
        )
    )


def get_edit_blocks(input_string):
    code_block_pattern = r"^\**(.*)\**\n```.*?\n<<<<<<< SEARCH\n([\S\s]*?)\n?=======\n([\S\s]*?)\n?>>>>>>> REPLACE\n```"
    matches = re.findall(code_block_pattern, input_string, re.MULTILINE)
    return matches


def apply_changes(file_list: List[Tuple[str, str, str]]):
    for file_path, search, replace in file_list:
        # If search block is empty, create a new file
        if not search:
            with open(file_path, "w", encoding="utf-8") as file:  # Create a new file
                file.write(replace)
        else:
            with open(file_path, "r+", encoding="utf-8") as file:
                content = file.read()
                updated_content = content.replace(search, replace)
                file.seek(0)
                file.write(updated_content)
                file.truncate()


class SelectCodeBlockMenu(TextMenu):
    def __init__(self, file: str, **kwargs):
        super().__init__(file=file, prompt="select block", **kwargs)
        self.select_all()

    def on_enter_pressed(self):
        self.close()


class FileListMenu(ListEditMenu):
    def __init__(self):
        super().__init__(
            prompt="file list",
            json_file=os.path.join(setting_dir, "context.json"),
            wrap_text=True,
        )
        self.add_command(self.delete_selected_item, hotkey="ctrl+k")

    def get_item_text(self, item: Any) -> str:
        file = item["file"]
        content = item["content"]
        if content:
            return f'{file}:\n{item["content"]}'
        else:
            return file

    def _add_file(self):
        menu = FileMenu(prompt="add file", goto=os.getcwd())
        file = menu.select_file()
        if file is not None:
            content: Optional[str]
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()

            select_code_block_menu = SelectCodeBlockMenu(file)
            select_code_block_menu.exec()
            if select_code_block_menu.is_cancelled:
                content = None
            else:
                lines = list(select_code_block_menu.get_selected_items())
                content = "\n".join(lines)

            self.add_file(file, content)

    def add_file(self, file: str, content: Optional[str] = None):
        if not os.path.isfile(file):
            raise FileNotFoundError(f'"{file}" does not exist')
        self.append_item({"file": file, "content": content})

    def get_file_list_string(self) -> str:
        result = []
        for item in self.items:
            file = item["file"]
            content = item["content"]
            if content is None:
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
            result.append(f"{file}\n```\n{content}\n```")
        return "\n".join(result)


class ApplyChangeMenu(ConfirmMenu):
    def __init__(self, **kwargs):
        super().__init__(prompt="apply changes?", wrap_text=True, **kwargs)

    def get_item_text(self, item: Any) -> str:
        file = item[0]
        search = item[1] + "\n" if item[1] else ""
        replace = item[2] + "\n" if item[2] else ""
        return f"{file}\n<<<<<<<\n{search}=======\n{replace}>>>>>>>"


class CoderMenu(ChatMenu):
    def __init__(self, files: Optional[List[str]] = None, **kwargs):
        super().__init__(data_file=os.path.join(setting_dir, "chat.json"), **kwargs)

        self.__file_list_menu = FileListMenu()

        if files:
            self.__clear_files()
            for file in files:
                self.__file_list_menu.add_file(file)

        self.add_command(self.__add_file, hotkey="alt+a")
        self.add_command(self.__apply_change, hotkey="alt+enter")
        self.add_command(self.__clear_files, hotkey="alt+x")
        self.add_command(self.__list_files, hotkey="alt+l")

        self.__update_message()

    def __add_file(self):
        self.__file_list_menu._add_file()
        self.__update_message()

    def __update_message(self):
        files = ", ".join(
            [os.path.basename(file["file"]) for file in self.__file_list_menu.items]
        )
        self.set_message(f"files: {files}")

    def __list_files(self):
        self.__file_list_menu.exec()
        self.__update_message()

    def __clear_files(self):
        self.__file_list_menu.clear()
        self.__update_message()

    def on_message(self, content: str):
        match = re.findall(r"```files\n([\S\s]+?)\n\s*```", content, flags=re.MULTILINE)
        if match:
            files = match[0].splitlines()
            menu = ListEditMenu(prompt="add files to context?", items=files)
            menu.exec()
            if not menu.is_cancelled and files:
                for file in files:
                    self.__file_list_menu.add_file(file)
                self.__update_message()

        self.__apply_change()

    def __apply_change(self):
        messages = self.get_messages()
        if len(messages) <= 0:
            return

        selected_line = self.get_selected_item()
        if selected_line is None:
            return

        selected_message = self.get_messages()[selected_line.message_index]
        content = selected_message["content"]

        blocks = get_edit_blocks(content)
        if len(blocks) > 0:
            menu = ApplyChangeMenu(items=blocks)
            menu.exec()
            if menu.is_confirmed():
                apply_changes(blocks)

    def on_enter_pressed(self):
        i = len(self.get_messages())
        if i == 0:
            task = self.get_input()

            if len(self.__file_list_menu.items) == 0:
                self.send_message(get_context_files(task=task))

            self.send_message(
                get_coding_prompt(
                    task=task,
                    file_list=self.__file_list_menu.get_file_list_string(),
                )
            )
        else:
            return super().on_enter_pressed()


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*")
    args = parser.parse_args()

    os.makedirs(setting_dir, exist_ok=True)
    CoderMenu(files=args.files).exec()


if __name__ == "__main__":
    _main()
