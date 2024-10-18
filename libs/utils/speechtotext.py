import json
import subprocess
from typing import Optional

from utils.platform import is_termux


def speech_to_text(allow_input=False) -> Optional[str]:
    if is_termux():
        out = subprocess.check_output(
            ["termux-dialog", "speech"], universal_newlines=True
        )
        data = json.loads(out)
        if data["code"] == 0:
            return data["text"]
        else:
            return None
    elif allow_input:
        return input("TTS is not supported, please input: ")
    else:
        raise Exception("Speech-to-text is not supported on the current platform.")
