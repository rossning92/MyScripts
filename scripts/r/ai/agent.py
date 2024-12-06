import argparse
import os
import re
from typing import Optional

from _shutil import exec_bash
from ML.gpt.chatmenu import ChatMenu
from utils.editor import edit_text
from utils.jsonutil import load_json, save_json
from utils.menu.confirmmenu import ConfirmMenu
from utils.template import render_template

SETTING_DIR = "tmp"
CONVERSATION_FILE = "chat.json"
SESSION_FILE = "agent_session.json"


def _get_prompt(task: str):
    return f"""\
1. You are my assistant to help me complete a task.
2. You can execute any bash command anytime to complete the task. To do so, provide a valid bash command in this format:
```bash
... bash command ...
```
and I'll then reply with the function's return value.

3. Once the task is completed, you must reply with the full result using the following format:
TASK COMPLETED
```
... result goes here...
```

Here's my task:
---
{task}
---
"""


class AgentMenu(ChatMenu):
    def __init__(self, task: Optional[str], yes_always=True, **kwargs):
        super().__init__(
            conv_file=os.path.join(SETTING_DIR, CONVERSATION_FILE),
            new_conversation=False,
            **kwargs,
        )

        self.__yes_always = yes_always
        self.__task = task

        self.__session_file = os.path.join(SETTING_DIR, SESSION_FILE)
        self.__session = load_json(self.__session_file, default={})

        self.task_result: Optional[str] = None

        self.add_command(self.__edit_task, hotkey="alt+p")

    def on_created(self):
        if self.__task:
            self.__complete_task(self.__task)

    def on_message(self, content: str):
        self.__check_code_blocks()

    def on_enter_pressed(self):
        i = len(self.get_messages())
        if i == 0:
            task = self.get_input()

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
            _get_prompt(
                task=task,
            )
        )

    def __check_code_blocks(self):
        messages = self.get_messages()
        if len(messages) <= 0:
            return

        selected_line = self.get_selected_item()
        if selected_line is None:
            return

        selected_message = self.get_messages()[selected_line.message_index]
        content = selected_message["content"]

        # Check if should run bash command
        response_message = ""
        blocks = re.findall(r"```bash\n([\S\s]+?)\n\s*```", content, flags=re.MULTILINE)
        if len(blocks) > 0:
            should_run = True
            if not self.__yes_always:
                menu = ConfirmMenu("run command?", items=blocks)
                menu.exec()
                should_run = menu.is_confirmed()

            if should_run:
                for block in blocks:
                    output = exec_bash(block, capture_output=True)
                    if output:
                        response_message = f"""\
The above command outputs:
```
{output}
```
"""
                    else:
                        response_message = "The above command finishes successfully."

        # Check if the task is completed
        result = re.findall(
            r"TASK COMPLETED\n```.*?\n([\S\s]+?)\n\s*```", content, flags=re.MULTILINE
        )
        if len(result) > 0:
            self.set_message(f"result: {result[0]}")
            self.task_result = result[0]
            if self.__task:
                self.close()

        if response_message:
            self.send_message(response_message)

    def __edit_task(self):
        task = self.__session["task"]
        new_task = self.call_func_without_curses(lambda: edit_text(task))
        if new_task != task:
            self.__complete_task(new_task)


def _main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", nargs="?", type=str)
    args = parser.parse_args()

    if args.task is None:
        task = None
    elif os.path.isfile(args.task):
        with open(args.task, "r", encoding="utf-8") as f:
            task = f.read()
            task = render_template(task, context=dict(os.environ))
    else:
        task = args.task

    os.makedirs(SETTING_DIR, exist_ok=True)

    menu = AgentMenu(yes_always=True, task=task)
    menu.exec()

    if task:
        print(menu.task_result)


if __name__ == "__main__":
    _main()
