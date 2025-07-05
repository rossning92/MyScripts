import argparse
import os
from typing import Any, Callable, Dict, List, Optional

from ai.agent import AgentMenu
from ai.filecontextmenu import FileContextMenu
from ai.tools.checkpoints import restore_files_to_timestamp
from ai.tools.read_file import read_file
from ai.tools.run_bash_command import run_bash_command
from ai.tools.search_and_replace import search_and_replace
from ai.tools.write_file import write_file


class CodeAgentMenu(AgentMenu):
    def __init__(self, files: Optional[List[str]], **kwargs):
        super().__init__(**kwargs)
        self.__file_context_menu = FileContextMenu(files=files)

    def get_tools(self) -> List[Callable]:
        return [read_file, write_file, search_and_replace, run_bash_command]

    def get_prompt(self) -> str:
        return super().get_prompt() + self.__file_context_menu.get_prompt()

    def undo_messages(self) -> List[Dict[str, Any]]:
        removed_messages = super().undo_messages()
        if len(removed_messages) > 0:
            timestamp = removed_messages[-1].get("__timestamp", None)
            if timestamp is not None:
                restore_files_to_timestamp(timestamp=timestamp)
        return removed_messages

    def get_status_text(self) -> str:
        return self.__file_context_menu.get_summary() + "\n" + super().get_status_text()


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
    args = parser.parse_args()

    files = _parse_files(args.files)

    menu = CodeAgentMenu(files)
    menu.exec()


if __name__ == "__main__":
    _main()
