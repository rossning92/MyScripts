import argparse
import os
import re
from io import StringIO
from typing import Any, AnyStr, Dict, List, Optional

from ai.codeeditutils import Change, apply_change_interactive, revert_changes
from ai.get_context_files import GetContextFilesMenu
from ML.gpt.chatmenu import ChatMenu
from utils.editor import edit_text
from utils.jsonutil import load_json, save_json
from utils.menu.confirmmenu import confirm
from utils.menu.filemenu import FileMenu
from utils.menu.listeditmenu import ListEditMenu
from utils.menu.textmenu import TextMenu

SETTING_DIR = ".coder"
CONVERSATION_FILE = "chat_v2.json"
SESSION_FILE = "session.json"


def _get_editing_prompt(task: str, context: str):
    return (
        """\
Act as an expert software developer.
Take requests for changes to the supplied code.
Output a copy of each file that needs changes


## Describe each change with a *SEARCH/REPLACE block*

All changes to files must use this *SEARCH/REPLACE block* format.
ONLY EVER RETURN CODE IN A *SEARCH/REPLACE BLOCK*!
Every *SEARCH/REPLACE block* must use this format:

filename.py
```
<<<<<<< SEARCH
... original code block ...
=======
... replaced code block ...
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
        + ("\n\nHere starts the code to be modified:\n\n" + context if context else "")
    )


def _find_changes(s: str):
    code_block_pattern = r"^\**(.+)\**\n```.*?\n<<<<<<< SEARCH\n([\S\s]*?)\n?=======\n([\S\s]*?)\n?>>>>>>> REPLACE\n```"
    matches = re.findall(code_block_pattern, s, re.MULTILINE)
    return [
        Change(file=match[0], search=match[1], replace=match[2]) for match in matches
    ]


class SelectCodeBlockMenu(TextMenu):
    def __init__(self, file: str, **kwargs):
        super().__init__(file=file, prompt="select block", **kwargs)
        self.select_all()

    def on_enter_pressed(self):
        self.close()


class FileListMenu(ListEditMenu):
    def __init__(self, files: List[str]):
        super().__init__(
            items=files,
            prompt="file list",
            wrap_text=True,
        )
        self.add_command(self.delete_selected_item, hotkey="ctrl+k")

    def get_item_text(self, item: Any) -> str:
        file = item["file"]
        if "content" in item and item["content"]:
            return f'{file}:\n{item["content"]}'
        else:
            return file

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
            with open(file, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
            assert start >= 1 and start <= end and end <= len(lines)
            content = "\n".join(lines[start - 1 : end])
            self.append_item({"file": file, "content": content})
        else:
            self.append_item({"file": file})

    def get_context(self) -> str:
        result = []
        for item in self.items:
            if "content" in item and item["content"]:
                content = item["content"]
            else:
                with open(item["file"], "r", encoding="utf-8") as f:
                    content = f.read()
            result.append(f'{item["file"]}\n```\n{content}\n```')
        return "\n".join(result)


class CoderMenu(ChatMenu):
    def __init__(self, files: Optional[List[str]] = None, **kwargs):
        # Create directory if it does not exist.
        os.makedirs(SETTING_DIR, exist_ok=True)
        with open(os.path.join(SETTING_DIR, ".gitignore"), "w") as f:
            f.write("*")

        super().__init__(
            conv_file=os.path.join(SETTING_DIR, CONVERSATION_FILE),
            new_conversation=False,
            **kwargs,
        )

        self.__modified_files: List[str] = []

        self.__session_file = os.path.join(SETTING_DIR, SESSION_FILE)
        self.__session: Dict[str, Any] = load_json(
            self.__session_file, default={"task": "", "files": []}
        )
        self.__file_list_menu = FileListMenu(files=self.__session["files"])

        if files:
            self.__clear_files()
            for file in files:
                self.__file_list_menu.add_file(file)

        self.add_command(self.__add_file, hotkey="alt+a")
        self.add_command(self.__apply_change, hotkey="alt+enter")
        self.add_command(self.__clear_files, hotkey="alt+x")
        self.add_command(self.__list_files, hotkey="alt+l")
        self.add_command(self.__undo, hotkey="ctrl+z")

        self.__update_prompt()

    def __add_file(self):
        self.__file_list_menu._add_file()
        self.__update_prompt()

    def __update_prompt(self):
        s = StringIO()
        s.write("task : " + self.__session["task"] + "\n")
        s.write(
            "files: "
            + "|".join(
                [
                    file["file"]
                    + ("(%d)" % len(file["content"]) if "content" in file else "")
                    for file in self.__file_list_menu.items
                ]
            )
            + "\n"
        )
        self.set_prompt(s.getvalue())

    def __list_files(self):
        self.__file_list_menu.exec()
        self.__update_prompt()

    def __clear_files(self):
        self.__file_list_menu.clear()
        self.__update_prompt()

    def on_message(self, content: str):
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

        changes = _find_changes(content)
        self.__modified_files[:] = apply_change_interactive(changes)

    def on_enter_pressed(self):
        i = len(self.get_messages())
        if i == 0:
            task = self.get_input()

            # Get context files
            if len(self.__file_list_menu.items) == 0 and confirm(
                "Search for relevant files to add to context"
            ):
                menu = GetContextFilesMenu(
                    task=task,
                    conv_file=os.path.join(SETTING_DIR, "chat_get_context_files.json"),
                )
                menu.exec()

                for file in menu.files:
                    self.__file_list_menu.add_file(file)
                self.__update_prompt()

            self.__complete_task(task=task)
        else:
            return super().on_enter_pressed()

    def __save_session(self):
        save_json(self.__session_file, self.__session)

    def __complete_task(self, task: str):
        self.__session["task"] = task
        self.__save_session()

        self.clear_messages()
        self.send_message(
            _get_editing_prompt(
                task=task,
                context=self.__file_list_menu.get_context(),
            )
        )

    def __revert_modified_files(self):
        revert_changes(self.__modified_files)
        self.__modified_files.clear()

    def __undo(self):
        task = self.__session["task"]
        new_task = self.call_func_without_curses(lambda: edit_text(task))
        if new_task != task:
            self.__revert_modified_files()
            self.__complete_task(new_task)


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*")
    args = parser.parse_args()

    # If only one context file is specified, change directory to the file folder.
    files = args.files
    if files and len(files) == 1 and os.path.isabs(files[0]):
        dir_name = os.path.dirname(files[0])
        os.chdir(dir_name)
        files[0] = os.path.basename(files[0])

    CoderMenu(files=files).exec()


if __name__ == "__main__":
    _main()
