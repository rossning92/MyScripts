import argparse
import os
import tempfile
from datetime import datetime
from email.mime import image
from pathlib import Path
from queue import Queue
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple

from ai.complete_chat import complete_chat
from ai.openai.complete_chat import create_user_message, message_to_str
from ai.tokenutil import token_count
from utils.clip import set_clip
from utils.editor import edit_text
from utils.gitignore import create_gitignore
from utils.historymanager import HistoryManager
from utils.jsonutil import load_json, save_json
from utils.menu import Menu
from utils.menu.filemenu import FileMenu
from utils.menu.jsoneditmenu import JsonEditMenu
from utils.menu.textmenu import TextMenu

_MODULE_NAME = Path(__file__).stem

_INTERRUPT_MESSAGE = "[INTERRUPTED]"


class SettingsMenu(JsonEditMenu):
    def __init__(self, settings_file: str, model: Optional[str]) -> None:
        self.__model = model
        super().__init__(json_file=settings_file)

    def get_default_values(self) -> Dict[str, Any]:
        return {"model": self.__model if self.__model else "gpt-4o"}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "model": Literal[
                "gpt-4o",
                "gpt-4o-mini",
                "o3-mini",
                "claude-3-7-sonnet-latest",
                "claude-sonnet-4-0",
                "claude-opus-4-0",
            ]
        }


class Line:
    def __init__(self, role: str, text: str, msg_index: int, subindex: int) -> None:
        self.role = role
        self.text = text
        self.msg_index = msg_index
        self.subindex = subindex  # subindex with in the message

    def __str__(self) -> str:
        if self.subindex == 0:
            return f"[{self.msg_index+1}] {self.text}"
        else:
            return self.text


class _SelectConvMenu(Menu[str]):
    def __init__(self, **kwargs) -> None:
        super().__init__(prompt="load conversation", **kwargs)

    def get_item_text(self, conv_file: str) -> str:
        conv = load_json(conv_file)
        return str(conv)


class ChatMenu(Menu[Line]):
    default_conv: Dict = {"messages": [], "timestamps": []}

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
        system_prompt: Optional[str] = None,
        settings_menu_class=SettingsMenu,
    ) -> None:
        self.__auto_create_conv_file = conv_file is None
        self.__conv_file = conv_file
        self.__copy_and_exit = copy_and_exit
        self.__first_message = message
        self.__image_file: Optional[str] = image_file
        self.__is_generating = False
        self.__last_yanked_line: Optional[Line] = None
        self.__lines: List[Line] = []
        self.__post_generation: Queue[Callable] = Queue()
        self.__prompt = prompt
        self.__system_prompt = system_prompt
        self.__yank_mode = 0

        self.__data_dir = (
            data_dir if data_dir else os.path.join(".config", _MODULE_NAME)
        )
        os.makedirs(self.__data_dir, exist_ok=True)
        create_gitignore(self.__data_dir)

        self.__settings_menu = settings_menu_class(
            settings_file=os.path.join(self.__data_dir, "settings.json"), model=model
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
        self.add_command(self.__edit_settings, hotkey="ctrl+s")
        self.add_command(self.__goto_next_message, hotkey="alt+n")
        self.add_command(self.__goto_prev_message, hotkey="alt+p")
        self.add_command(self.__load_conversation, hotkey="ctrl+l")
        self.add_command(self.__view_system_prompt)
        self.add_command(self.__yank, hotkey="ctrl+y")
        self.add_command(self.new_conversation, hotkey="ctrl+n")
        self.add_command(self.undo_messages, hotkey="ctrl+z")

        self.__conversations_dir = os.path.join(self.__data_dir, "conversations")
        os.makedirs(self.__conversations_dir, exist_ok=True)
        self.__history_manager = HistoryManager(
            save_dir=self.__conversations_dir,
            prefix="conversation_",
            ext=".json",
        )

        self.__conv: Dict[str, Any] = ChatMenu.default_conv.copy()  # conversation data

        self.new_conversation()
        if new_conversation:
            pass
        elif self.__conv_file is not None:
            if not new_conversation and os.path.exists(self.__conv_file):
                self.load_conversation(conv_file)
        else:  # load last conversation
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
        msg_index = self.__lines[index].msg_index
        start = -1
        stop = -1
        text = []
        for i, line in enumerate(self.__lines):
            if line.msg_index == msg_index:
                if start == -1:
                    start = i
                stop = i
                text.append(line.text)
        set_clip("\n".join(text))
        self.set_selection(start, stop)
        self.set_message("message copied")
        return

    def __edit_message(self, first_user_message=False):
        msg_index = -1
        if first_user_message:
            for i, message in enumerate(self.get_messages()):
                if message["role"] == "user":
                    msg_index = i
                    break
        else:
            selected = self.get_selected_item()
            if selected:
                msg_index = selected.msg_index
        if msg_index < 0:
            self.set_message("Cannot find message to edit")
            return

        message = self.get_messages()[msg_index]
        content = message["content"]
        new_content = self.call_func_without_curses(lambda: edit_text(content))
        if new_content != content:
            message["content"] = new_content

            # Delete all messages after.
            del self.get_messages()[msg_index + 1 :]

            self.__populate_lines()

            if message["role"] == "user":
                self.__complete_chat()

    def __edit_settings(self):
        self.__settings_menu.exec()

    def __goto_message(self, direction: Literal["next", "prev"]):
        i = self.get_selected_index()
        if i < 0:
            return

        if direction == "next":
            range_params = (i + 1, len(self.__lines), 1)
        else:  # direction == "prev"
            range_params = (i - 1, -1, -1)

        for j in range(*range_params):
            if (
                self.__lines[j].subindex == 0
                and self.__lines[j].msg_index != self.__lines[i].msg_index
            ):
                self.set_selected_item(self.__lines[j])
                return

    def __goto_next_message(self):
        self.__goto_message("next")

    def __goto_prev_message(self):
        self.__goto_message("prev")

    def __edit_prompt(self):
        self.__edit_message(first_user_message=True)

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

    def undo_messages(self) -> List[Tuple[Dict[str, Any], float]]:
        removed_messages: List[Tuple[Dict[str, Any], float]] = []
        messages = self.get_messages()
        if messages:
            removed_messages.append((messages.pop(), self.__conv["timestamps"].pop()))
        while messages and messages[-1]["role"] != "assistant":
            removed_messages.append((messages.pop(), self.__conv["timestamps"].pop()))
        self.__populate_lines()
        return removed_messages

    def __update_prompt(self):
        prompt = f"{self.__prompt}"
        if self.__image_file:
            prompt += f" ({os.path.basename(self.__image_file)})"
        self.set_prompt(prompt)

    def __view_system_prompt(self):
        if self.__system_prompt:
            TextMenu(text=self.__system_prompt, prompt="System Prompt").exec()
        else:
            self.set_message("No system prompt set")

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

    def get_item_color(self, item: Line) -> str:
        return "white" if item.role == "assistant" else "blue"

    def get_messages(self) -> List[Dict[str, Any]]:
        return self.__conv["messages"]

    def on_created(self):
        if self.__first_message is not None:
            self.send_message(self.__first_message)

    def send_message(self, text: str) -> None:
        if self.__is_generating:
            return

        self.clear_input()

        if text:
            self.append_user_message(text)

        # Reset image file
        self.__image_file = None
        self.__update_prompt()

        self.__complete_chat()

    def __append_message(self, message: Dict[str, Any]):
        self.get_messages().append(message)
        self.__conv["timestamps"].append(datetime.now().timestamp())
        assert len(self.get_messages()) == len(self.__conv["timestamps"])

    def append_user_message(self, text: str):
        msg_index = len(self.get_messages())
        self.__append_message(
            create_user_message(text=text, image_file=self.__image_file)
        )
        for i, text in enumerate(text.splitlines()):
            self.append_item(
                Line(role="user", text=text, msg_index=msg_index, subindex=i)
            )
        self.save_conversation()
        self.update_screen()

    def __complete_chat(self):
        if self.__is_generating:
            return

        self.__is_generating = True

        content = ""
        msg_index = len(self.get_messages())
        interrupted = False
        line = Line(role="assistant", text="", msg_index=msg_index, subindex=0)
        subindex = 1
        self.append_item(line)
        try:
            for chunk in complete_chat(
                self.get_messages(),
                model=self.__get_model(),
                system_prompt=self.__system_prompt,
            ):
                content += chunk
                for i, a in enumerate(chunk.split("\n")):
                    if i > 0:
                        line = Line(
                            role="assistant",
                            text="",
                            msg_index=msg_index,
                            subindex=subindex,
                        )
                        subindex += 1
                        self.append_item(line)
                    line.text += a

                self.update_screen()
                self.process_events(raise_keyboard_interrupt=True)
        except KeyboardInterrupt:
            interrupted = True
            content += f"\n{_INTERRUPT_MESSAGE}"
            self.append_item(
                Line(
                    role="assistant",
                    text=f"{_INTERRUPT_MESSAGE}",
                    msg_index=msg_index,
                    subindex=subindex,
                )
            )

        self.__append_message(
            {
                "role": "assistant",
                "content": content,
            }
        )
        self.__is_generating = False
        self.save_conversation()

        if not interrupted:
            self.on_message(content)

            if self.__copy_and_exit:
                set_clip(content)
                self.close()

            while not self.__post_generation.empty():
                (self.__post_generation.get())()

    def save_conversation(self):
        if self.__conv_file is None:
            return
        os.makedirs(os.path.dirname(self.__conv_file), exist_ok=True)
        save_json(self.__conv_file, self.__conv)
        self.__history_manager.delete_old_files()

    def __populate_lines(self):
        self.__lines.clear()
        for msg_index, message in enumerate(self.get_messages()):
            for i, line in enumerate(message_to_str(message).splitlines()):
                self.append_item(
                    Line(
                        role=message["role"],
                        text=line,
                        msg_index=msg_index,
                        subindex=i,
                    )
                )
        self.update_screen()

    def load_conversation(self, file: Optional[str] = None):
        if file is not None:
            self.__conv_file = file

        if not self.__conv_file:
            return

        if not os.path.exists(self.__conv_file):
            self.set_message(f"Conv file not exist: {self.__conv_file}")
            return

        self.__conv = load_json(self.__conv_file, default=ChatMenu.default_conv.copy())
        self.__populate_lines()

    def clear_messages(self):
        self.__lines.clear()
        self.get_messages().clear()
        self.__conv["timestamps"].clear()
        token_count.clear()
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
        try:
            self.__cancel_chat_completion()
            self.send_message(self.get_input())
        except KeyboardInterrupt:
            self.__post_generation.put(
                lambda message=self.get_input(): self.send_message(message)
            )
            raise

    def on_item_selection_changed(self, item: Optional[Line], i: int):
        self.__yank_mode = 0
        return super().on_item_selection_changed(item, i)

    def on_message(self, content: str):
        pass

    def get_status_text(self) -> str:
        return f"""CHAT : tokIn={token_count.input_tokens} tokOut={token_count.output_tokens} cfg={str(self.__settings_menu.data)}
{super().get_status_text()}"""

    def on_escape_pressed(self):
        self.__cancel_chat_completion()

    def __cancel_chat_completion(self):
        if self.__is_generating:
            raise KeyboardInterrupt()

    def paste(self) -> bool:
        if not super().paste():
            from PIL import Image, ImageGrab

            im = ImageGrab.grabclipboard()
            if isinstance(im, Image.Image):
                with tempfile.NamedTemporaryFile(
                    suffix=".jpg", delete=False
                ) as temp_file:
                    im.save(temp_file.name)
                    self.__image_file = temp_file.name
                    self.__update_prompt()
                    return True

        return False


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

    image_file: Optional[str] = None
    message: Optional[str] = None
    if args.input and os.path.isfile(args.input):
        if args.input.endswith(".jpg") or args.input.endswith(".png"):
            image_file = args.input
        else:
            with open(args.input, "r", encoding="utf-8") as f:
                message = f.read()
    else:
        message = args.input

    chat = ChatMenu(message=message, image_file=image_file)
    chat.exec()


if __name__ == "__main__":
    _main()
