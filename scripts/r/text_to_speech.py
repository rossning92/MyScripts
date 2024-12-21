import subprocess

from utils.platform import is_termux


def text_to_speech(text: str):
    if is_termux():
        subprocess.check_call(["termux-tts-speak", text])
    else:
        from ai.openai.text_to_speech import text_to_speech as text_to_speech_openai

        text_to_speech_openai(text=text)
