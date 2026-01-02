import subprocess
import time
import urllib.parse
from typing import Callable, List

from ai.agent_menu import AgentMenu
from utils.clip import set_clip
from utils.shutil import shell_open


def open_file(file: str):
    shell_open(file)


def open_url(url: str):
    shell_open(url)


def navigate_to(destination: str):
    encoded_destination = urllib.parse.quote(destination)
    open_url(
        f"https://www.google.com/maps/dir/?api=1&travelmode=driving&destination={encoded_destination}"
    )


def type_text(text: str):
    set_clip(text)

    # Go to the previous app
    subprocess.call("su -c input keyevent 187", shell=True)
    subprocess.call("su -c input keyevent 187", shell=True)

    time.sleep(1.0)
    subprocess.call("su -c input keyevent 279", shell=True)  # paste


class AssistantMenu(AgentMenu):
    def on_created(self):
        self.voice_input()

    def get_tools_callable(self) -> List[Callable]:
        return super().get_tools_callable() + [
            open_file,
            open_url,
            navigate_to,
            type_text,
        ]


if __name__ == "__main__":
    AssistantMenu().exec()
