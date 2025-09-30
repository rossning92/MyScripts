import argparse
import os
from platform import platform
from typing import Any, Callable, Dict, List, Optional

import ai.agent_menu
from ai.agent_menu import AgentMenu
from ai.filecontextmenu import FileContextMenu
from ai.message import Message
from ai.tools import Settings
from ai.tools.edit_file import edit_file
from ai.tools.glob_files import glob_files
from ai.tools.grep_tool import grep_tool
from ai.tools.list_files import list_files
from ai.tools.read_file import read_file
from ai.tools.run_bash_command import run_bash_command
from utils.checkpoints import (
    get_oldest_files_since_timestamp,
    restore_files_since_timestamp,
)
from utils.editor import edit_text_file
from utils.menu.filemenu import FileMenu
from utils.shutil import start_process

README_FILE = "README.md"

# DEFAULT_MODEL = "claude-3-7-sonnet-latest"
DEFAULT_MODEL = "gpt-5-codex(low)"


def get_env_info() -> str:
    return f"""# Environment Information

Platform: {platform()}
Working directory: {os.getcwd()}
"""


class SettingsMenu(ai.agent_menu.SettingsMenu):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__update_settings()

    def get_default_values(self) -> Dict[str, Any]:
        return {
            **super().get_default_values(),
            "need_confirm": True,
            "auto_open_diff": False,
        }

    def on_dict_update(self, data):
        super().on_dict_update(data)
        self.__update_settings()

    def __update_settings(self):
        Settings.need_confirm = self.data["need_confirm"]


class CodeAgentMenu(AgentMenu):
    def __init__(
        self,
        files: Optional[List[str]],
        model=DEFAULT_MODEL,
        settings_menu_class=SettingsMenu,
        **kwargs,
    ):
        super().__init__(
            data_dir=os.path.join(".config", "coder"),
            model=model,
            settings_menu_class=settings_menu_class,
            **kwargs,
        )
        self.__file_context_menu = FileContextMenu(files=files)
        self.add_command(self.__add_file, hotkey="@")
        self.add_command(self.__edit_instructions)
        self.add_command(self.__open_diff, hotkey="ctrl+d")

    def __edit_instructions(self):
        self.call_func_without_curses(
            lambda: edit_text_file(os.path.join(self.get_data_dir(), README_FILE))
        )

    def __get_readme_content(self) -> str:
        file = os.path.join(self.get_data_dir(), README_FILE)
        if not os.path.exists(file):
            return ""

        with open(file, "r", encoding="utf-8") as f:
            s = f.read().strip()
        if not s:
            return ""

        return f"""# General Instructions

{s}
"""

    def __open_diff(self):
        messages = self.get_messages()
        if len(messages) == 0:
            self.set_message("No messages found")

        for history_dir, rel_path in get_oldest_files_since_timestamp(
            messages[0]["timestamp"]
        ):
            full_path = os.path.join(history_dir, rel_path)
            start_process(["code", "--diff", full_path, rel_path])

    def get_tools(self) -> List[Callable]:
        return [
            read_file,
            edit_file,
            run_bash_command,
            list_files,
            glob_files,
            grep_tool,
        ]

    def get_system_prompt(self) -> str:
        return "\n".join(
            s
            for s in [
                super().get_system_prompt(),
                self.__get_readme_content(),
                self.__file_context_menu.get_prompt(),
                get_env_info(),
            ]
            if s
        )

    def undo_messages(self) -> List[Message]:
        removed_messages = super().undo_messages()
        for message in reversed(removed_messages):
            restore_files_since_timestamp(timestamp=message["timestamp"])
        return removed_messages

    def get_status_text(self) -> str:
        files = self.__file_context_menu.get_status_text()
        return (files + "\n" if files else "") + super().get_status_text()

    def __add_file(self):
        file_menu = FileMenu()
        file = file_menu.select_file()
        if file:
            cwd = os.getcwd()
            if os.path.commonpath([cwd, file]) == cwd:
                path = os.path.relpath(file, cwd)
            else:
                path = file
            self.insert_text(f"`{path}` ")

    def on_result(self, result: str):
        if self.get_setting("auto_open_diff"):
            self.__open_diff()


def _parse_files(files: List[str]) -> List[str]:
    # If only one file is specified, switch to its directory.
    if files and len(files) == 1 and os.path.isabs(files[0]):
        dir_name = os.path.dirname(files[0])
        os.chdir(dir_name)
        files[0] = os.path.basename(files[0])
    return files


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*")
    parser.add_argument(
        "-d",
        "--dir",
        type=str,
        help="Source root directory",
        default=os.environ.get("SOURCE_ROOT"),
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default=DEFAULT_MODEL,
    )
    args = parser.parse_args()

    if args.dir:
        if not os.path.exists(args.dir):
            os.makedirs(args.dir, exist_ok=True)
        os.chdir(args.dir)

    files = _parse_files(args.files)

    menu = CodeAgentMenu(files, model=args.model)
    menu.exec()


if __name__ == "__main__":
    _main()
