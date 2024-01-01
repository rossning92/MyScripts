import os
import re
from typing import Dict, List, Optional

from _shutil import load_json, save_json
from ai.openai.chat_completion import chat_completion
from utils.clip import set_clip
from utils.menu import Menu


class _Message:
    def __init__(self, role: str, text: str) -> None:
        self.role = role
        self.text = text

    def __str__(self) -> str:
        return f"{self.role[0]}: {self.text}"


def extract_code_from_markdown(s: str) -> List[str]:
    code_blocks = re.findall(r"```(?:.*?)\n([\s\S]*?)\n```", s)
    return code_blocks


class ChatMenu(Menu[_Message]):
    def __init__(self, first_message: Optional[str] = None) -> None:
        self.__messages: List[_Message] = []
        super().__init__(
            items=self.__messages,
            search_mode=False,
            wrap_text=True,
            highlight={"^u:": "blue"},
            prompt=">"
            # line_number=False,
        )
        self.__first_message = first_message

        self.add_command(self.start_new_chat, hotkey="ctrl+n")
        self.add_command(self.__yank_message, hotkey="ctrl+y")
        self.add_command(self.__delete_message, hotkey="ctrl+k")

    def on_created(self):
        if self.__first_message is not None:
            self.__send_message(self.__first_message)

    def __get_messages(self) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]
        for m in self.__messages:
            messages.append({"role": m.role, "content": m.text})
        return messages

    def __send_message(self, text: str) -> None:
        m = _Message(role="user", text=text)
        self.append_item(m)

        messages = self.__get_messages()

        m = _Message(role="assistant", text="")
        self.append_item(m)

        for chunk in chat_completion(messages):
            m.text += chunk
            self.update_screen()
            self.process_events()

        self.save_chat()

    def __get_data_file(self) -> str:
        return os.path.join(
            os.environ["MY_DATA_DIR"], "chatgpt_start_conversation.json"
        )

    def save_chat(self):
        save_json(
            self.__get_data_file(),
            {
                "messages": [
                    {"role": m.role, "content": m.text} for m in self.__messages
                ]
            },
        )

    def load_chat(self):
        if os.path.isfile(self.__get_data_file()):
            data = load_json(self.__get_data_file())
            self.__messages.clear()

            for m in data["messages"]:
                self.append_item(_Message(role=m["role"], text=m["content"]))

    def start_new_chat(self):
        self.__messages.clear()
        self.update_screen()

    def on_enter_pressed(self):
        text = self.get_input()
        self.__send_message(text)
        self.clear_input()

    def __yank_message(self):
        message = self.get_selected_item()
        if message is not None:
            code_block = extract_code_from_markdown(message.text)
            if len(code_block) > 0:
                set_clip(code_block[0])
                self.set_message("code copied.")
            else:
                set_clip(message.text)
                self.set_message("message copied.")

    def __delete_message(self):
        idx = self.get_selected_index()
        if idx >= 0:
            del self.__messages[idx]
            self.save_chat()
            self.update_screen()


if __name__ == "__main__":
    chat = ChatMenu()
    chat.load_chat()
    chat.exec()
