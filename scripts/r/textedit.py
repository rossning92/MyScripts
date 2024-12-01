import subprocess
from typing import List

from utils.menu import Menu


class TextEdit(Menu[str]):
    def __init__(self):
        self.lines: List[str] = []
        super().__init__(items=self.lines, search_mode=False)
        self.add_command(self.__voice_input, hotkey="alt+i")
        self.add_command(self.__fix, hotkey="alt+f")
        self.add_command(self.__delete_line, hotkey="ctrl+k")

    def __voice_input(self):
        try:
            from r.speech_to_text import speech_to_text

            text = speech_to_text()
        except Exception as e:
            self.set_message(f"ERROR: {e}")
            return

        if not text:
            return

        self.set_input(text)
        self.append_item(text)
        self.update_screen()

    def __fix(self):
        i = self.get_selected_index()
        if i < 0:
            return

        out = subprocess.check_output(
            [
                "run_script",
                "r/ai/openai/complete_chat.py",
                "Fix the spelling and grammar of the following text and only return the corrected text:\n---\n"
                + self.lines[i],
            ],
            universal_newlines=True,
        )
        out = out.strip()
        self.lines[i] = out
        self.update_screen()

    def __delete_line(self):
        i = self.get_selected_index()
        del self.lines[i]
        self.update_screen()

    def on_enter_pressed(self):
        line = self.get_input().strip()
        self.clear_input()
        self.append_item(line)
        self.update_screen()


TextEdit().exec()
