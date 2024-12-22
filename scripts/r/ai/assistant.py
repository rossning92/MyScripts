from agent import AgentMenu
from ai.openai.speech_to_text import speech_to_text
from ai.openai.text_to_speech import text_to_speech


class AssistantMenu(AgentMenu):
    def on_enter_pressed(self):
        text = self.get_input()
        if not text:
            self.__listen()
        else:
            super().on_enter_pressed()

    def __listen(self):
        text = speech_to_text()
        if text:
            self.send_message(text)

    def on_created(self):
        super().on_created()

    def on_response(self, text: str, done: bool):
        text_to_speech(text)


if __name__ == "__main__":
    AssistantMenu().exec()
