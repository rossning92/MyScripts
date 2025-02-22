from typing import Callable, List

from ai.agent import AgentMenu
from ai.openai.speech_to_text import speech_to_text
from ai.openai.text_to_speech import text_to_speech
from utils.email import send_email


class AssistantMenu(AgentMenu):
    def on_enter_pressed(self):
        text = self.get_input()
        if not text:
            self.__listen()
        else:
            super().on_enter_pressed()

    def __listen(self):
        text = self.call_func_without_curses(lambda: speech_to_text())
        if text:
            self.send_message(text)

    def on_created(self):
        super().on_created()
        self.__listen()

    def on_response(self, text: str, done: bool):
        text_to_speech(text)
        if not done:
            self.__listen()

    def get_tools(self) -> List[Callable]:
        return super().get_tools() + [send_email]


if __name__ == "__main__":
    AssistantMenu().exec()
