import os
import tempfile
from typing import Optional

from audio.record_audio import record_audio

from utils.menu.asynctaskmenu import AsyncTaskMenu


class RecordMenu(AsyncTaskMenu):
    def __init__(self, out_file: Optional[str] = None):
        self.__out_file = out_file if out_file else tempfile.mktemp(suffix=".wav")
        self.space_pressed = False
        super().__init__(
            target=lambda stop_event: record_audio(
                out_file=self.__out_file, stop_event=stop_event
            ),
            prompt="(Recording...)",
        )
        self.add_command(self.__on_space_pressed, hotkey="space")

    def on_close(self):
        super().on_close()
        if self.is_cancelled and os.path.exists(self.__out_file):
            os.remove(self.__out_file)

    def get_output_file(self) -> Optional[str]:
        return None if self.is_cancelled else self.__out_file

    def __on_space_pressed(self):
        self.space_pressed = True
        self.close()
