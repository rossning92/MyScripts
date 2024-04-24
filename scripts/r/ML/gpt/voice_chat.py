from ai.openai.speech_to_text import speech_to_text
from ai.openai.text_to_speech import text_to_speech
from ML.gpt.chatgpt_deprecated import Chat


def voice_chat():
    chat = Chat()

    try:
        while True:
            message = speech_to_text()
            reply = chat.send(message)
            text_to_speech(reply)

    except (KeyboardInterrupt, EOFError):
        pass


if __name__ == "__main__":
    voice_chat()
