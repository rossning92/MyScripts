import os
from threading import Event, Thread
from typing import Callable, List

from ai.agent import AgentMenu
from ai.openai.speech_to_text import convert_audio_to_text
from ai.openai.text_to_speech import text_to_speech
from utils.menu.recordmenu import RecordMenu
from utils.menu.textmenu import TextMenu
from utils.shutil import shell_open


def open_file(file: str):
    shell_open(file)


def open_url(url: str):
    shell_open(url)


class TtsMenu(TextMenu):
    def __init__(self, text: str):
        super().__init__(prompt="speaking... (press 'space' to dismiss)", text=text)

        self.__cancel_event = Event()

        self.__tts_thread = Thread(
            target=text_to_speech,
            kwargs={"text": text, "cancel_event": self.__cancel_event},
        )
        self.__tts_thread.start()

        self.add_command(self.__dismiss, hotkey="space")

    def on_idle(self):
        if not self.__tts_thread.is_alive():
            self.close()

    def on_close(self):
        self.__cancel_event.set()

    def __dismiss(self):
        self.close()


class AssistantMenu(AgentMenu):
    def __init__(self, **kwargs):
        super().__init__(load_last_agent=True, **kwargs)

        self.add_command(self.__listen, hotkey="space")

    def on_enter_pressed(self):
        text = self.get_input()
        if not text:
            self.__listen()
        else:
            super().on_enter_pressed()

    def __listen(self):
        menu = RecordMenu()
        menu.exec()
        out_file = menu.get_output_file()
        if not out_file:
            return

        if not os.path.exists(out_file):
            return

        try:
            text = convert_audio_to_text(file=out_file)
        except ValueError as ex:
            self.set_message(str(ex))
            return

        os.remove(out_file)
        if text:
            self.send_message(text)

    def on_response(self, text: str, done: bool):
        if text:
            TtsMenu(text=text).exec()
        if not done:
            self.__listen()

    def get_tools(self) -> List[Callable]:
        return super().get_tools() + [open_file, open_url]


if __name__ == "__main__":
    AssistantMenu().exec()
