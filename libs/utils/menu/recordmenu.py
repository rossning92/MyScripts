import logging
import os
from typing import Optional

from audio.record_audio import record_audio

from utils.menu.asynctaskmenu import AsyncTaskMenu


class RecordMenu(AsyncTaskMenu):
    def __init__(self, out_file: Optional[str] = None):
        self.space_pressed = False
        super().__init__(
            target=lambda stop_event: record_audio(
                out_file=out_file, stop_event=stop_event
            ),
            prompt="recording",
        )
        self.add_command(self.__on_space_pressed, hotkey="space")

    def on_close(self):
        super().on_close()

        out_file = self.get_result()
        if not out_file:
            return

        file_exists = os.path.exists(out_file)
        if not file_exists:
            return

        if self.is_cancelled:
            os.remove(out_file)
        else:
            logging.debug(
                "Saved recording file size: %d bytes", os.path.getsize(out_file)
            )

    def get_output_file(self) -> Optional[str]:
        return self.get_result() if not self.is_cancelled else None

    def __on_space_pressed(self):
        self.space_pressed = True
        self.close()
