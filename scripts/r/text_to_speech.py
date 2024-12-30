import os
import subprocess

from utils.platform import is_termux


def text_to_speech(text: str):
    if is_termux():
        with open(os.devnull, "w") as devnull:
            ps = subprocess.Popen(
                ["termux-tts-speak", text],
                stdin=subprocess.PIPE,
                stdout=devnull,
                stderr=devnull,
            )
            assert ps.stdin is not None
            ps.stdin.write(text.encode())
            ps.stdin.close()
            ret = ps.wait()
            if ret != 0:
                raise Exception(
                    "Text-to-speech process failed with return code: {}".format(ret)
                )

    else:
        from ai.openai.text_to_speech import text_to_speech as text_to_speech_openai

        text_to_speech_openai(text=text)
