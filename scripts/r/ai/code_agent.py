import argparse
from typing import Callable, List

from ai.agent import AgentMenu
from ai.tools.read_file import read_file
from ai.tools.run_bash_command import run_bash_command
from ai.tools.search_and_replace import search_and_replace
from ai.tools.write_file import write_file


class CodeAgentMenu(AgentMenu):
    def get_tools(self) -> List[Callable]:
        return [read_file, write_file, search_and_replace, run_bash_command]


def _main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    menu = CodeAgentMenu()
    menu.exec()


if __name__ == "__main__":
    _main()
