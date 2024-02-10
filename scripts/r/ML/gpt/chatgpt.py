import os
import re
from typing import Dict, List, Optional

from _shutil import load_json, save_json
from ai.openai.chat_completion import chat_completion
from utils.clip import set_clip
from utils.menu import Menu


class _Line:
    def __init__(self, role: str, text: str, message_index: int) -> None:
        self.role = role
        self.text = text
        self.color = "yellow" if role == "user" else "white"
        self.message_index = message_index

    def __str__(self) -> str:
        return self.text


def extract_code_from_markdown(s: str) -> List[str]:
    code_blocks = re.findall(r"```(?:.*?)\n([\s\S]*?)\n```", s)
    return code_blocks


class ChatMenu(Menu[_Line]):
    def __init__(
        self, first_message: Optional[str] = None, model: Optional[str] = None
    ) -> None:
        self.__model = model
        self.__lines: List[_Line] = []
        self.__messages: List[Dict[str, str]] = []
        super().__init__(
            items=self.__lines,
            search_mode=False,
            wrap_text=True,
            prompt=">",
            line_number=True,
        )
        self.__first_message = first_message
        self.__last_yanked_line: Optional[_Line] = None
        self.__yank_mode = 0

        self.add_command(self.start_new_chat, hotkey="ctrl+n")
        self.add_command(self.__yank, hotkey="ctrl+y")

        self.start_new_chat()

    def on_created(self):
        if self.__first_message is not None:
            self.__send_message(self.__first_message)

    def __send_message(self, text: str) -> None:
        message_index = len(self.__messages)
        self.__messages.append({"role": "user", "content": text})
        for s in text.splitlines():
            self.append_item(_Line(role="user", text=s, message_index=message_index))

        response = ""
        message_index = len(self.__messages)
        line = _Line(role="assistant", text="", message_index=message_index)
        self.append_item(line)
        for chunk in chat_completion(self.__messages, model=self.__model):
            response += chunk
            for i, a in enumerate(chunk.split("\n")):
                if i > 0:
                    line = _Line(role="assistant", text="", message_index=message_index)
                    self.append_item(line)
                line.text += a

            self.update_screen()
            self.process_events()

        self.__messages.append({"role": "assistant", "content": response})
        self.save_chat()

    def __get_data_file(self) -> str:
        return os.path.join(
            os.environ["MY_DATA_DIR"], "chatgpt_start_conversation.json"
        )

    def save_chat(self):
        save_json(self.__get_data_file(), {"messages": self.__messages})

    def load_chat(self):
        if os.path.isfile(self.__get_data_file()):
            data = load_json(self.__get_data_file())
            self.__messages = data["messages"]

            for message_index, message in enumerate(self.__messages):
                if message["role"] != "system":
                    for line in message["content"].splitlines():
                        self.append_item(
                            _Line(
                                role=message["role"],
                                text=line,
                                message_index=message_index,
                            )
                        )

    def start_new_chat(self):
        self.__lines.clear()
        self.__messages = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]
        self.update_screen()

    def on_enter_pressed(self):
        text = self.get_input()
        self.clear_input()
        self.__send_message(text)

    def __yank(self):
        indices = list(self.get_selected_indices())
        if len(indices) == 1:
            idx = indices[0]
            line = self.__lines[idx]
            if line != self.__last_yanked_line:
                self.__yank_mode = 0
                self.__last_yanked_line = line

            if self.__yank_mode == 0:
                set_clip(line.text)
                self.set_message(f"line {idx+1} copied")
                self.__yank_mode = 1

            elif self.__yank_mode == 1:
                message = self.__messages[line.message_index]
                message_text = message["content"]
                code_block = extract_code_from_markdown(message_text)
                if len(code_block) > 0:
                    set_clip(code_block[0])
                    self.set_message("code copied")
                else:
                    set_clip(message_text)
                    self.set_message("message copied")
                self.__yank_mode = 0
        elif len(indices) > 1:
            line_text = []
            for idx in indices:
                line = self.__lines[idx]
                line_text.append(line.text)
            set_clip("\n".join(line_text))
            self.set_message("selected line copied")
            self.set_multi_select(False)


if __name__ == "__main__":
    chat = ChatMenu()
    chat.load_chat()
    chat.exec()
