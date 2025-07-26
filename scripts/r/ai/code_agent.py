import argparse
import os
from platform import platform
from typing import Any, Callable, Dict, List, Optional

from ai.agent import AgentMenu
from ai.filecontextmenu import FileContextMenu
from ai.tools import Settings
from ai.tools.checkpoints import restore_files_to_timestamp
from ai.tools.edit_file import edit_file
from ai.tools.glob_files import glob_files
from ai.tools.read_file import read_file
from ai.tools.run_bash_command import run_bash_command
from ai.tools.write_file import write_file
from ML.gpt.chatmenu import SettingsMenu
from tree import tree
from utils.menu.filemenu import FileMenu


def get_env_info() -> str:
    file_tree = tree(os.getcwd(), max_level=1)

    return f"""# Environment Information

Platform: {platform()}
Current working directory: {os.getcwd()}
File tree:
```
{file_tree}
```
"""


class _SettingsMenu(SettingsMenu):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__update_settings()

    def get_default_values(self) -> Dict[str, Any]:
        return {**super().get_default_values(), "need_confirm": True}

    def on_dict_update(self, data):
        super().on_dict_update(data)
        self.__update_settings()

    def __update_settings(self):
        Settings.need_confirm = self.data["need_confirm"]


class CodeAgentMenu(AgentMenu):
    def __init__(self, files: Optional[List[str]], **kwargs):
        super().__init__(
            data_dir=".coder",
            model="claude-3-7-sonnet-latest",
            settings_menu_class=_SettingsMenu,
            **kwargs,
        )
        self.__file_context_menu = FileContextMenu(files=files)
        self.add_command(self.__add_file, hotkey="@")
        self.add_command(self.__open_file_menu, hotkey="alt+f")

    def get_tools(self) -> List[Callable]:
        return [read_file, write_file, edit_file, run_bash_command, glob_files]

    def get_prompt(self) -> str:
        return "\n\n".join(
            s
            for s in [
                super().get_prompt(),
                self.__file_context_menu.get_prompt(),
                get_env_info(),
            ]
            if s
        )

    def undo_messages(self) -> List[Dict[str, Any]]:
        removed_messages = super().undo_messages()
        if len(removed_messages) > 0:
            timestamp = removed_messages[-1].get("__timestamp", None)
            if timestamp is not None:
                restore_files_to_timestamp(timestamp=timestamp)
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

    def __open_file_menu(self):
        FileMenu(goto=os.getcwd()).exec()


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
    args = parser.parse_args()

    if args.dir:
        os.chdir(args.dir)
    else:
        default_dir = os.path.expanduser("~/TestProject")
        os.makedirs(default_dir, exist_ok=True)
        os.chdir(default_dir)

    files = _parse_files(args.files)

    menu = CodeAgentMenu(files)
    menu.exec()


if __name__ == "__main__":
    _main()
