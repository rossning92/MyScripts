import argparse
from typing import Callable, List, Optional

from ai.agent import AgentMenu
from ai.filecontextmenu import FileContextMenu
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


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*")
    args = parser.parse_args()

    menu = CodeAgentMenu(files=args.files)
    menu.exec()


if __name__ == "__main__":
    _main()
