import os
import tempfile
from threading import Event, Thread
from typing import Optional

from audio.record_audio import record_audio

from utils.menu import Menu


class RecordMenu(Menu):
    def __init__(self, out_file: Optional[str] = None):
        super().__init__(prompt="recording...")

        self.__stop_event = Event()
        self.__out_file = out_file if out_file else tempfile.mktemp(suffix=".wav")
        self.__record_thread = Thread(
            target=record_audio,
            kwargs={"out_file": self.__out_file, "stop_event": self.__stop_event},
        )
        self.__record_thread.start()

        self.add_command(self.__done, hotkey="space")

    def __done(self):
        self.close()

    def on_close(self):
        self.__stop_event.set()
        self.__record_thread.join()
        if self.is_cancelled and os.path.exists(self.__out_file):
            os.remove(self.__out_file)

    def get_output_file(self) -> Optional[str]:
        return None if self.is_cancelled else self.__out_file
