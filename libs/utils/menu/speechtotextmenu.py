import os

from utils.fileutils import human_readable_size

from .asynctaskmenu import AsyncTaskMenu


class SpeechToTextMenu(AsyncTaskMenu):
    def __init__(self, out_file: str):
        from ai.openai.speech_to_text import convert_audio_to_text

        self.out_file = out_file
        size_str = human_readable_size(os.path.getsize(out_file))
        super().__init__(
            lambda: convert_audio_to_text(file=out_file),
            prompt=f"converting audio (size={size_str}) to text",
        )
