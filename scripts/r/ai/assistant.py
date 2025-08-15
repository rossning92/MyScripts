import os
import time
from typing import Callable, List

from ai.agentmenu import AgentMenu
from ai.openai.speech_to_text import convert_audio_to_text
from ai.openai.text_to_speech import text_to_speech
from utils.menu.asynctaskmenu import AsyncTaskMenu
from utils.menu.recordmenu import RecordMenu
from utils.shutil import shell_open


def open_file(file: str):
    shell_open(file)


def open_url(url: str):
    shell_open(url)


class AssistantMenu(AgentMenu):
    def __init__(self, **kwargs):
        self.__last_escape_pressed = 0.0
        super().__init__(**kwargs)

    def on_enter_pressed(self):
        text = self.get_input()
        if not text:
            self.__listen()
        else:
            super().on_enter_pressed()

    def on_created(self):
        self.__listen()

    def __listen(self):
        menu = RecordMenu()
        menu.exec()
        out_file = menu.get_output_file()
        if not out_file:
            return

        if not os.path.exists(out_file):
            return

        menu = AsyncTaskMenu(
            lambda: convert_audio_to_text(file=out_file),
            prompt="convert audio to text",
        )
        try:
            menu.exec()
        except ValueError as ex:
            self.set_message(str(ex))
            return

        os.remove(out_file)
        text = menu.get_result()
        if text:
            self.send_message(text)

    def on_response(self, text: str, done: bool):
        if text:
            AsyncTaskMenu(
                items=text.splitlines(),
                prompt="speaking",
                search_mode=False,
                target=lambda stop_event: text_to_speech(
                    text=text, stop_event=stop_event
                ),
                wrap_text=True,
            ).exec()
        if not done:
            self.__listen()

    def get_tools(self) -> List[Callable]:
        return super().get_tools() + [open_file, open_url]

    def on_escape_pressed(self):
        now = time.time()
        if now - self.__last_escape_pressed <= 1.0:
            self.new_conversation()
        self.__last_escape_pressed = now


if __name__ == "__main__":
    AssistantMenu().exec()
