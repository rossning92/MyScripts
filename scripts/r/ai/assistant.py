from typing import Callable, List

from ai.agent_menu import AgentMenu
from utils.shutil import shell_open


def open_file(file: str):
    shell_open(file)


def open_url(url: str):
    shell_open(url)


class AssistantMenu(AgentMenu):
    def on_created(self):
        self.voice_input()

    def get_tools(self) -> List[Callable]:
        return super().get_tools() + [open_file, open_url]


if __name__ == "__main__":
    AssistantMenu().exec()
