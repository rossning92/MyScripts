from agent import AgentMenu
from ai.openai.speech_to_text import speech_to_text
from ai.openai.text_to_speech import text_to_speech


class AssistantMenu(AgentMenu):
    def on_enter_pressed(self):
        self.__listen()

    def __listen(self):
        text = self.call_func_without_curses(lambda: speech_to_text())
        if text:
            self.send_message(text)

    def on_created(self):
        super().on_created()
        self.__listen()

    def on_response(self, text: str):
        text_to_speech(text)
        self.__listen()


if __name__ == "__main__":
    AssistantMenu().exec()
