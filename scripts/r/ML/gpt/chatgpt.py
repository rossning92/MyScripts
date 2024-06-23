import argparse
import os
import subprocess
import tempfile
from typing import Any, Dict, List, Optional

from _shutil import load_json, save_json
from ai.openai.complete_chat import chat_completion
from utils.clip import set_clip
from utils.menu import Menu

MAX_CONVERSATIONS = 25


class _Line:
    def __init__(self, role: str, text: str, message_index: int) -> None:
        self.role = role
        self.text = text
        self.color = "yellow" if role == "user" else "white"
        self.message_index = message_index

    def __str__(self) -> str:
        return self.text


class ChatMenu(Menu[_Line]):
    def __init__(
        self,
        message: Optional[str] = None,
        model: Optional[str] = None,
        copy_result_and_exit=False,
        new_conversation=True,
    ) -> None:
        self.__model = model
        self.__lines: List[_Line] = []
        self.__data: Dict[str, Any] = {"conversations": [{"messages": []}]}
        super().__init__(
            items=self.__lines,
            search_mode=False,
            wrap_text=True,
            prompt=">",
            line_number=True,
        )
        self.__first_message = message
        self.__last_yanked_line: Optional[_Line] = None
        self.__yank_mode = 0
        self.__copy_result_and_exit = copy_result_and_exit

        self.add_command(self.__delete_current_message, hotkey="delete")
        self.add_command(self.__edit_message, hotkey="ctrl+e")
        self.add_command(self.__load_conversation, hotkey="ctrl+l")
        self.add_command(self.__yank, hotkey="ctrl+y")
        self.add_command(self.new_conversation, hotkey="ctrl+n")

        self.load_conversations()
        if new_conversation:
            self.new_conversation()

    def __load_conversation(self):
        menu = Menu(items=[c for c in self.__data["conversations"]])
        menu.exec()
        selected_index = menu.get_selected_index()
        if selected_index >= 0:
            conv = self.__data["conversations"]
            conv.insert(0, conv.pop(selected_index))
            self.populate_lines()

    def get_messages(self) -> List[Dict[str, str]]:
        return self.__data["conversations"][0]["messages"]

    def on_created(self):
        if self.__first_message is not None:
            self.__send_message(self.__first_message)

            if self.__copy_result_and_exit:
                message = self.get_messages()[-1]["content"]
                set_clip(message)
                self.close()

    def __send_message(self, text: str) -> None:
        message_index = len(self.get_messages())
        self.get_messages().append({"role": "user", "content": text})
        self.save_conversations()
        for s in text.splitlines():
            self.append_item(_Line(role="user", text=s, message_index=message_index))

        self.__get_response()

    def __get_response(self):
        response = ""
        message_index = len(self.get_messages())
        line = _Line(role="assistant", text="", message_index=message_index)
        self.append_item(line)
        for chunk in chat_completion(self.get_messages(), model=self.__model):
            response += chunk
            for i, a in enumerate(chunk.split("\n")):
                if i > 0:
                    line = _Line(role="assistant", text="", message_index=message_index)
                    self.append_item(line)
                line.text += a

            self.update_screen()
            self.process_events()

        self.get_messages().append({"role": "assistant", "content": response})
        self.save_conversations()

    def __get_data_file(self) -> str:
        return os.path.join(os.environ["MY_DATA_DIR"], "chatgpt_conversations.json")

    def save_conversations(self):
        save_json(self.__get_data_file(), self.__data)

    def populate_lines(self):
        self.__lines.clear()
        if len(self.__data["conversations"]) > 0:
            for message_index, message in enumerate(self.get_messages()):
                if message["role"] != "system":
                    for line in message["content"].splitlines():
                        self.append_item(
                            _Line(
                                role=message["role"],
                                text=line,
                                message_index=message_index,
                            )
                        )
        self.update_screen()

    def load_conversations(self):
        if os.path.isfile(self.__get_data_file()):
            self.__data = load_json(self.__get_data_file())
            self.populate_lines()

    def new_conversation(self):
        if len(self.get_messages()) > 0:
            self.__lines.clear()
            conversations = self.__data["conversations"]
            while len(conversations) >= MAX_CONVERSATIONS:
                # Remove the oldest conversation
                del conversations[-1]
            conversations.insert(0, {"messages": []})
            self.update_screen()

    def on_enter_pressed(self):
        text = self.get_input()
        self.clear_input()
        self.__send_message(text)

    def get_status_bar_text(self) -> str:
        s = "%d" % len(self.__data["conversations"])
        return s + " | " + super().get_status_bar_text()

    def __copy_block(self, index: int):
        # Check if it's in the code block; if so, copy all the code.
        is_code_block = False
        start = -1
        stop = -1
        text: List[str] = []
        for i, line in enumerate(self.__lines):
            if line.text.startswith("```"):
                is_code_block = not is_code_block
                if is_code_block:
                    start = i + 1
                else:
                    stop = i - 1
                    if start <= index <= stop:
                        set_clip("\n".join(text))
                        self.set_selection(start, stop)
                        self.set_message("code copied")
                        return
            elif is_code_block:
                text.append(line.text)

        # Copy the whole message.
        message_index = self.__lines[index].message_index
        start = -1
        stop = -1
        text = []
        for i, line in enumerate(self.__lines):
            if line.message_index == message_index:
                if start == -1:
                    start = i
                stop = i
                text.append(line.text)
        set_clip("\n".join(text))
        self.set_selection(start, stop)
        self.set_message("message copied")
        return

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
                index = self.get_selected_index()
                if index >= 0:
                    self.__copy_block(index=index)
        elif len(indices) > 1:
            line_text = []
            for idx in indices:
                line = self.__lines[idx]
                line_text.append(line.text)
            set_clip("\n".join(line_text))
            self.set_message("selected line copied")
            self.set_multi_select(False)

    def __delete_current_message(self):
        selected_line = self.get_selected_item()
        if selected_line is not None:
            del self.get_messages()[selected_line.message_index]
            self.populate_lines()

    def __edit_text(self, text: str):
        with tempfile.NamedTemporaryFile(
            suffix=".tmp", mode="w+", delete=False, encoding="utf-8"
        ) as tmp_file:
            tmp_file.write(text)
            tmp_filename = tmp_file.name

        subprocess.call(["nvim", tmp_filename])

        with open(tmp_filename, "r", encoding="utf-8") as f:
            new_text = f.read()
        return new_text

    def __edit_message(self):
        selected_line = self.get_selected_item()
        if selected_line is not None:
            message_index = selected_line.message_index
            selected_message = self.get_messages()[message_index]
            content = selected_message["content"]
            new_content = self.call_func_without_curses(
                lambda: self.__edit_text(content)
            )
            if new_content != content:
                selected_message["content"] = new_content

                # Delete all messages after.
                del self.get_messages()[message_index + 1 :]

                self.populate_lines()

                if selected_message["role"] == "user":
                    self.__get_response()


def complete_chat(
    *,
    input_text: str,
    prompt_text: Optional[str] = None,
    model: Optional[str] = None,
):
    if os.path.isfile(input_text):
        with open(input_text, "r", encoding="utf-8") as f:
            input_text = f.read()

    if prompt_text:
        input_text = prompt_text + ":\n---\n" + input_text

    chat = ChatMenu(
        message=input_text,
        copy_result_and_exit=True,
        model=model,
    )
    chat.exec()


def _main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=str, nargs="?")
    args = parser.parse_args()

    if args.input is None:
        s = None
    elif os.path.isfile(args.input):
        with open(args.input, "r", encoding="utf-8") as f:
            s = f.read()
    else:
        s = args.input

    chat = ChatMenu(message=s, new_conversation=False)
    chat.exec()


if __name__ == "__main__":
    _main()
