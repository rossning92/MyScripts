import subprocess

from ai.openai.tts import tts as tts_openai
from utils.platform import is_termux


def tts(text: str, **kwargs):
    if is_termux():
        subprocess.run(["su", "-c", "input keyevent 127"])

    tts_openai(text=text, **kwargs)
