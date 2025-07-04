import argparse
import os
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from ai.complete_chat import complete_chat
from ai.openai.complete_chat import create_user_message, message_to_str
from utils.clip import set_clip
from utils.editor import edit_text
from utils.historymanager import HistoryManager
from utils.jsonutil import load_json, save_json
from utils.menu import Menu
from utils.menu.filemenu import FileMenu
from utils.menu.jsoneditmenu import JsonEditMenu


class _Line:
    def __init__(self, role: str, text: str, message_index: int) -> None:
        self.role = role
        self.text = text
        self.message_index = message_index

    def __str__(self) -> str:
        return self.text


class _SelectConvMenu(Menu[str]):
    def get_item_text(self, conv_file: str) -> str:
        conv = load_json(conv_file)
        return str(conv)


class ChatMenu(Menu[_Line]):
    default_conv: Dict = {"messages": []}

    def __init__(
        self,
        conv_file: Optional[str] = None,
        copy_and_exit=False,
        data_dir: Optional[str] = None,
        message: Optional[str] = None,
        model: Optional[str] = None,
        image_file: Optional[str] = None,
        new_conversation=True,
        prompt: str = "c",
    ) -> None:
        self.__auto_create_conv_file = conv_file is None
        self.__copy_and_exit = copy_and_exit
        self.__first_message = message
        self.__image_file: Optional[str] = image_file
        self.__is_generating = False
        self.__last_yanked_line: Optional[_Line] = None
        self.__lines: List[_Line] = []
        self.__prompt = prompt
        self.__yank_mode = 0

        self.__data_dir = (
            data_dir if data_dir else os.path.join(os.environ["MY_DATA_DIR"], "chat")
        )
        os.makedirs(self.__data_dir, exist_ok=True)

        self.__settings_file = os.path.join(self.__data_dir, "settings.json")
        self.__settings_menu = JsonEditMenu(
            json_file=self.__settings_file,
            default={"model": model if model else "gpt-4o"},
            schema={
                "model": Literal["gpt-4o", "o3-mini", "claude-3-7-sonnet-20250219"]
            },
        )

        super().__init__(
            items=self.__lines,
            search_mode=False,
            wrap_text=True,
            line_number=True,
        )

        self.add_command(self.__add_image, hotkey="alt+i")
        self.add_command(self.__edit_message, hotkey="alt+e")
        self.add_command(self.__edit_prompt, hotkey="alt+p")
        self.add_command(self.__load_conversation, hotkey="ctrl+l")
        self.add_command(self.__edit_settings, hotkey="ctrl+s")
        self.add_command(self.undo_messages, hotkey="ctrl+z")
        self.add_command(self.__yank, hotkey="ctrl+y")
        self.add_command(self.new_conversation, hotkey="ctrl+n")

        self.__conversations_dir = os.path.join(
            os.environ["MY_DATA_DIR"], "conversations"
        )
        os.makedirs(self.__conversations_dir, exist_ok=True)
        self.__history_manager = HistoryManager(
            save_dir=self.__conversations_dir,
            prefix="conversation_",
            ext=".json",
        )

        self.__conv: Dict[str, Any] = ChatMenu.default_conv.copy()  # conversation data
        self.__conv_file: str

        self.new_conversation()
        if conv_file:
            self.__conv_file = conv_file
            if not new_conversation and os.path.exists(self.__conv_file):
                self.load_conversation(conv_file)
        elif not new_conversation:
            conversation_files = self.__history_manager.get_all_files()
            if len(conversation_files) > 0:
                self.load_conversation(conversation_files[-1])

        self.__update_prompt()

    def __add_image(self):
        menu = FileMenu()
        self.__image_file = menu.select_file()
        self.__update_prompt()

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
                    text.clear()
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

    def __edit_message(self, message_index=-1):
        if message_index < 0:
            selected_line = self.get_selected_item()
            if selected_line is not None:
                message_index = selected_line.message_index
            else:
                return

        message = self.get_messages()[message_index]
        content = message["content"]
        new_content = self.call_func_without_curses(lambda: edit_text(content))
        if new_content != content:
            message["content"] = new_content

            # Delete all messages after.
            del self.get_messages()[message_index + 1 :]

            self.populate_lines()

            if message["role"] == "user":
                self.__complete_chat()

    def __edit_settings(self):
        self.__settings_menu.exec()

    def __edit_prompt(self):
        self.__edit_message(message_index=0)

    def __get_model(self) -> str:
        return self.__settings_menu.data["model"]

    def __load_conversation(self):
        menu = _SelectConvMenu(
            items=[f for f in self.__history_manager.get_all_files_desc()]
        )
        menu.exec()
        selected = menu.get_selected_item()
        if selected:
            self.load_conversation(selected)

    def undo_messages(self) -> List[Dict[str, Any]]:
        removed_messages: List[Dict[str, Any]] = []
        messages = self.get_messages()
        if messages:
            removed_messages.append(messages.pop())
        while messages and messages[-1]["role"] != "assistant":
            removed_messages.append(messages.pop())
        self.populate_lines()
        return removed_messages

    def __update_prompt(self):
        prompt = f"{self.__prompt}"
        if self.__image_file:
            prompt += f" ({os.path.basename(self.__image_file)})"
        self.set_prompt(prompt)

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

    def get_item_color(self, item: _Line) -> str:
        return "blue" if item.role == "user" else "white"

    def get_messages(self) -> List[Dict[str, Any]]:
        return self.__conv["messages"]

    def on_created(self):
        if self.__first_message is not None:
            self.send_message(self.__first_message)

    def send_message(self, text: str) -> None:
        if self.__is_generating:
            return

        self.clear_input()
        message_index = len(self.get_messages())
        self.get_messages().append(
            create_user_message(text=text, image_file=self.__image_file)
        )

        # Reset image file
        self.__image_file = None
        self.__update_prompt()

        self.save_conversation()
        for s in text.splitlines():
            self.append_item(_Line(role="user", text=s, message_index=message_index))

        self.__complete_chat()

    def __complete_chat(self):
        if self.__is_generating:
            return

        self.__is_generating = True

        content = ""
        messages = self.get_messages()
        message_index = len(self.get_messages())
        line = _Line(role="assistant", text="", message_index=message_index)
        self.append_item(line)
        for chunk in complete_chat(self.get_messages(), model=self.__get_model()):
            content += chunk
            for i, a in enumerate(chunk.split("\n")):
                if i > 0:
                    line = _Line(role="assistant", text="", message_index=message_index)
                    self.append_item(line)
                line.text += a

            self.update_screen()
            self.process_events(raise_keyboard_interrupt=True)
            if not self.__is_generating:
                break

        messages.append(
            {
                "role": "assistant",
                "content": content,
                "timestamp": datetime.now().timestamp(),
            }
        )

        self.__is_generating = False

        self.save_conversation()
        self.on_message(content)

        if self.__copy_and_exit:
            set_clip(content)
            self.close()

    def save_conversation(self):
        os.makedirs(os.path.dirname(self.__conv_file), exist_ok=True)
        save_json(self.__conv_file, self.__conv)
        self.__history_manager.delete_old_files()

    def populate_lines(self):
        self.__lines.clear()
        for message_index, message in enumerate(self.get_messages()):
            if message["role"] != "system":
                for line in message_to_str(message).splitlines():
                    self.append_item(
                        _Line(
                            role=message["role"],
                            text=line,
                            message_index=message_index,
                        )
                    )
        self.update_screen()

    def load_conversation(self, file: Optional[str] = None):
        if file is not None:
            self.__conv_file = file

        if not os.path.exists(self.__conv_file):
            self.set_message(f"Conv file not exist: {self.__conv_file}")
            return

        self.__conv = load_json(self.__conv_file, default=ChatMenu.default_conv.copy())
        self.populate_lines()

    def clear_messages(self):
        self.__lines.clear()
        self.__conv["messages"].clear()
        self.update_screen()

    def new_conversation(self, message: Optional[str] = None):
        self.clear_messages()

        if self.__auto_create_conv_file:
            self.__conv_file = self.__history_manager.get_new_file()

        if message:
            self.send_message(message)
        else:
            self.update_screen()

    def on_enter_pressed(self):
        self.send_message(self.get_input())

    def on_item_selection_changed(self, item: Optional[_Line], i: int):
        self.__yank_mode = 0
        return super().on_item_selection_changed(item, i)

    def on_message(self, content: str):
        pass

    def get_status_bar_text(self) -> str:
        return super().get_status_bar_text() + str(self.__settings_menu.data)

    def on_escape_pressed(self):
        if self.__is_generating:
            self.set_message("interrupt")
            self.__is_generating = False


def complete_chat_gui(
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
        copy_and_exit=True,
        model=model,
    )
    chat.exec()


def _main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=str, nargs="?")
    parser.add_argument("--image-file", type=str, nargs="?")
    args = parser.parse_args()

    if args.input is None:
        s = None
    elif os.path.isfile(args.input):
        with open(args.input, "r", encoding="utf-8") as f:
            s = f.read()
    else:
        s = args.input

    chat = ChatMenu(message=s, image_file=args.image_file)
    chat.exec()


if __name__ == "__main__":
    _main()
