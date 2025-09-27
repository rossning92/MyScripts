import argparse
import glob
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from pprint import pformat
from queue import Queue
from typing import Any, Callable, Dict, Iterator, List, Literal, Optional, Tuple

from ai.chat import complete_chat, get_tool_result_text, get_tool_use_text
from ai.message import Message
from ai.tokenutil import token_count
from ai.tool_use import ToolResult, ToolUse
from utils.clip import set_clip
from utils.dateutil import format_timestamp
from utils.editor import edit_text
from utils.gitignore import create_gitignore
from utils.historymanager import HistoryManager
from utils.jsonutil import load_json, save_json
from utils.menu import Menu
from utils.menu.confirmmenu import confirm
from utils.menu.exceptionmenu import ExceptionMenu
from utils.menu.filemenu import FileMenu
from utils.menu.jsoneditmenu import JsonEditMenu
from utils.menu.textmenu import TextMenu
from utils.platform import is_termux
from utils.slugify import slugify
from utils.textutil import is_text_file, truncate_text

_MODULE_NAME = Path(__file__).stem

_INTERRUPT_MESSAGE = "[INTERRUPTED]"


_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

MODELS = Literal[
    "gpt-5",
    "gpt-5(low)",
    "gpt-5-chat-latest",
    "gpt-5-codex",
    "gpt-5-codex(low)",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4o",
    "gpt-4o-mini",
    "o3-mini",
    "claude-3-7-sonnet-latest",
    "claude-sonnet-4-0",
    "claude-opus-4-0",
]
DEFAULT_MODEL = "gpt-4.1"


def _get_prompt_dir() -> str:
    prompt_dir = os.environ.get("PROMPT_DIR")
    if prompt_dir:
        return prompt_dir

    prompt_dir = os.path.join(_SCRIPT_DIR, "prompts")
    return prompt_dir


class SettingsMenu(JsonEditMenu):
    def __init__(self, json_file: str, model: Optional[str]) -> None:
        super().__init__(json_file=json_file)

        if model:
            self.data["model"] = model

    def get_default_values(self) -> Dict[str, Any]:
        return {"model": DEFAULT_MODEL, "web_search": False}

    def get_schema(self) -> Dict[str, Any]:
        return {"model": MODELS, "web_search": bool}


class Line:
    def __init__(
        self,
        role: str,
        msg_index: int,
        subindex: int,
        text: str = "",
        tool_use: Optional[ToolUse] = None,
        tool_result: Optional[ToolResult] = None,
    ) -> None:
        self.role = role
        self.text = text
        self.msg_index = msg_index
        self.subindex = subindex  # subindex with in the message
        self.tool_use = tool_use
        self.tool_result = tool_result

    def __str__(self) -> str:
        if self.tool_use:
            return get_tool_use_text(self.tool_use)
        elif self.tool_result:
            return get_tool_result_text(self.tool_result)
        else:
            return self.text


class _ChatItem:
    def __init__(
        self,
        path: str,
    ) -> None:
        self.path = path
        messages = load_json(path, default=[])

        file_name = os.path.splitext(os.path.basename(path))[0]
        self.text = " ".join((m["text"] for m in messages))
        self.preview = (
            format_timestamp(os.path.getmtime(path))
            + ": "
            + file_name
            + ": "
            + truncate_text(self.text)
        )

    def __str__(self) -> str:
        return self.text


class _SelectChatMenu(Menu[_ChatItem]):
    def __init__(self, chat_dir: str) -> None:
        self.__chat_dir = chat_dir
        super().__init__(prompt="Load history chat")
        self.__refresh()
        self.add_command(self.__delete_chat, hotkey="ctrl+k")

    def __refresh(self):
        self.items[:] = [
            _ChatItem(f)
            for f in reversed(
                sorted(
                    glob.glob(os.path.join(self.__chat_dir, "*.json")),
                    key=os.path.getmtime,
                )
            )
        ]

    def __delete_chat(self):
        chats = self.get_selected_items()
        if chats and confirm("Delete chat?"):
            for chat in chats:
                os.remove(chat.path)
            self.__refresh()

    def get_item_text(self, item: _ChatItem) -> str:
        return item.preview

    def match_item(self, patt: str, item: _ChatItem, index: int) -> int:
        return super().match_item(patt, item, index)


class ChatMenu(Menu[Line]):
    def __init__(
        self,
        chat_file: Optional[str] = None,
        copy=False,
        data_dir: Optional[str] = None,
        edit_text=False,
        message: Optional[str] = None,
        model: Optional[str] = None,
        attachment: Optional[str] = None,
        new_chat=True,
        out_file: Optional[str] = None,
        prompt: str = "u",
        system_prompt="",
        settings_menu_class=SettingsMenu,
    ) -> None:
        self.__auto_create_chat_file = chat_file is None
        self.__chat_file = chat_file
        self.__copy = copy
        self.__edit_text = edit_text
        self.__first_message = message
        self.__attachment: Optional[str] = attachment
        self.__is_generating = False
        self.__last_yanked_line: Optional[Line] = None
        self.__lines: List[Line] = []
        self.__after_chat_completion: Queue[Callable] = Queue()
        self.__prompt = prompt
        self.__out_file = out_file
        self.__system_prompt = system_prompt
        self.__yank_mode = 0

        self.__data_dir = (
            data_dir if data_dir else os.path.join(".config", _MODULE_NAME)
        )
        os.makedirs(self.__data_dir, exist_ok=True)
        create_gitignore(self.__data_dir)

        self.__settings_menu = settings_menu_class(
            json_file=os.path.join(self.__data_dir, "settings.json"),
            model=model,
        )

        super().__init__(
            items=self.__lines,
            search_mode=False,
            wrap_text=True,
            line_number=True,
            follow=True,
        )

        self.add_command(self.__add_attachment, hotkey="alt+a")
        self.add_command(self.__edit_message, hotkey="alt+e")
        self.add_command(self.__edit_prompt, hotkey="alt+p")
        self.add_command(self.__edit_settings, hotkey="alt+s")
        self.add_command(self.__go_up_message, hotkey="alt+u")
        self.add_command(self.__go_down_message, hotkey="alt+d")
        self.add_command(self.__load_chat, hotkey="ctrl+l")
        self.add_command(self.__load_prompt, hotkey="tab")
        self.add_command(self.__save_prompt)
        self.add_command(self.__save_chat_as)
        self.add_command(self.__show_more, hotkey="alt+m")
        self.add_command(self.__take_photo, hotkey="alt+i")
        self.add_command(self.__view_system_prompt)
        self.add_command(self.__yank, hotkey="ctrl+y")
        self.add_command(self.new_chat, hotkey="ctrl+n")
        self.add_command(self.save_chat, hotkey="ctrl+s")
        self.add_command(self.undo_messages, hotkey="ctrl+z")

        self.__chat_dir = os.path.join(self.__data_dir, "conversations")
        self.__history_manager = HistoryManager(
            save_dir=self.__chat_dir,
            prefix="chat_",
            ext=".json",
        )

        self.__messages: List[Message] = []

        self.new_chat()
        if new_chat:
            pass
        elif self.__chat_file is not None:
            if not new_chat and os.path.exists(self.__chat_file):
                self.load_chat(chat_file)
        else:  # load last chat
            files = self.__history_manager.get_all_files()
            if len(files) > 0:
                self.load_chat(files[-1])

        self.__update_prompt()

    def __add_attachment(self):
        menu = FileMenu()
        self.__attachment = menu.select_file()
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

    def __edit_message(self, message_index=-1):
        if message_index < 0:
            selected = self.get_selected_item()
            if selected:
                message_index = selected.msg_index
        if message_index < 0:
            self.set_message("Cannot find any message to edit")
            return

        message = self.get_messages()[message_index]
        content = message["text"]
        new_content = self.call_func_without_curses(lambda: edit_text(content))
        if new_content != content:
            message["text"] = new_content

            # Delete all messages after.
            del self.get_messages()[message_index + 1 :]

            self.__refresh_lines()

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

    def __go_down_message(self):
        self.__goto_message("next")

    def __go_up_message(self):
        self.__goto_message("prev")

    def __edit_prompt(self):
        self.__edit_message(message_index=0)

    def __save_chat_as(self):
        if not self.__chat_file:
            self.set_message("Current chat is empty")
            return

        menu = FileMenu(
            prompt="Save chat as",
            goto=self.__chat_dir,
            show_size=False,
            allow_cd=False,
        )
        chat_file = menu.select_new_file(ext=".json")
        if not chat_file:
            return

        chat_file = slugify(chat_file)
        save_json(chat_file, self.__messages)
        self.__chat_file = chat_file
        self.set_message(f"Chat saved to {chat_file}")

    def __save_prompt(self):
        messages = self.get_messages()
        if len(messages) == 0:
            self.set_message("No messages found")
            return

        message = messages[0]  # first message
        content = message["text"]

        menu = FileMenu(
            prompt="Save prompt to file",
            goto=_get_prompt_dir(),
            show_size=False,
            allow_cd=False,
        )
        prompt_file = menu.select_new_file(ext=".md")
        if not prompt_file:
            return

        prompt_file = slugify(prompt_file)
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(content)

    def __load_chat(self):
        menu = _SelectChatMenu(chat_dir=self.__chat_dir)
        menu.exec()
        selected = menu.get_selected_item()
        if selected:
            self.load_chat(selected.path)

    def __load_prompt(self):
        menu = FileMenu(
            prompt="Load prompt",
            goto=_get_prompt_dir(),
            show_size=False,
            recursive=True,
            allow_cd=False,
        )
        prompt_file = menu.select_file()
        if not prompt_file:
            return

        with open(prompt_file, "r", encoding="utf-8") as f:
            message = f.read()

        self.send_message(message)

    def __show_more(self):
        selected = self.get_selected_item()
        if selected:
            if selected.tool_result:
                tool_result_content = selected.tool_result["content"]
                TextMenu(text=tool_result_content, prompt="Tool result").exec()
            elif selected.tool_use:
                args = pformat(selected.tool_use["args"], sort_dicts=False)
                TextMenu(text=args, prompt="Tool use args").exec()

    def __take_photo(self):
        if not is_termux():
            self.set_message("Taking photo is only supported in Android")
            return

        tmp_photo = os.path.join(tempfile.gettempdir(), "photo.jpg")
        try:
            subprocess.run(
                ["termux-camera-photo", "-c", "0", tmp_photo],
                check=True,
            )
        except Exception as e:
            self.set_message(f"Failed to take photo: {e}")
            return

        self.__attachment = tmp_photo
        self.__update_prompt()

    def undo_messages(self) -> List[Message]:
        removed_messages: List[Message] = []
        messages = self.get_messages()
        if messages:
            removed_messages.append(messages.pop())
        self.__refresh_lines()
        if removed_messages:
            if removed_messages[-1]["role"] == "user":
                self.set_input(removed_messages[-1]["text"])
            else:
                self.clear_input()
        return removed_messages

    def __update_prompt(self):
        prompt = f"{self.__prompt}"
        if self.__attachment:
            prompt += " ({})".format(os.path.basename(self.__attachment))
        self.set_prompt(prompt)

    def __view_system_prompt(self):
        system_prompt = self.get_system_prompt()
        if system_prompt:
            TextMenu(text=system_prompt, prompt="System Prompt").exec()
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

    def get_line_number_text(self, item_index: int) -> str:
        item = self.items[item_index]
        line_number_text = f"{item.msg_index+1}"
        if item.subindex == 0:
            return line_number_text
        else:
            return " " * len(line_number_text)

    def get_item_color(self, item: Line) -> str:
        return "white" if item.role == "assistant" else "blue"

    def get_messages(self) -> List[Message]:
        return self.__messages

    def get_setting(self, name: str) -> Any:
        return self.__settings_menu.data[name]

    def on_created(self):
        if self.__first_message is not None:
            self.send_message(self.__first_message)

    def send_message(
        self,
        text: str,
        tool_results: Optional[List[ToolResult]] = None,
    ) -> None:
        if self.__is_generating:
            return

        self.clear_input()

        if text or tool_results:
            self.append_user_message(text, tool_results=tool_results)

        self.__attachment = None
        self.__update_prompt()

        self.__complete_chat()

    def append_user_message(
        self,
        text: str,
        tool_results: Optional[List[ToolResult]] = None,
    ):
        msg_index = len(self.get_messages())

        image_file = None
        if self.__attachment:
            ext = os.path.splitext(self.__attachment)[1]
            if is_text_file(self.__attachment):
                with open(self.__attachment, "r", encoding="utf-8") as f:
                    context = f.read()

                if self.__edit_text:
                    text = f"""Edit the input text according to my instructions. You should only return the result, do not include any other text.

Following is the input text:
<input_text>
{context.rstrip()}
</input_text>

Following is my instructions:
<instructions>
{text.rstrip()}
</instructions>
"""
                else:
                    text = f"""{text.rstrip()}

You should reply based on the provided context:
<context>
{context.rstrip()}
</context>
"""

            elif ext in (".jpg", ".jpeg", ".png", ".gif"):
                image_file = self.__attachment
            else:
                raise Exception(f"Unsupported attachment type: {ext}")

        message = Message(
            role="user",
            text=text,
            timestamp=datetime.now().timestamp(),
        )
        subindex = 0
        for text in text.splitlines():
            self.append_item(
                Line(role="user", text=text, msg_index=msg_index, subindex=subindex)
            )
            subindex += 1

        if image_file:
            message["image_file"] = image_file
        if tool_results:
            message["tool_result"] = tool_results

            for tool_result in tool_results:
                self.append_item(
                    Line(
                        role="user",
                        msg_index=msg_index,
                        subindex=subindex,
                        tool_result=tool_result,
                    )
                )

        self.get_messages().append(message)

        self.save_chat()
        self.update_screen()

    def complete_chat(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Callable[..., Any]]] = None,
        on_tool_use_start: Optional[Callable[[ToolUse], None]] = None,
        on_tool_use_args_delta: Optional[Callable[[str], None]] = None,
        on_tool_use: Optional[Callable[[ToolUse], None]] = None,
    ) -> Iterator[str]:
        return complete_chat(
            messages,
            model,
            system_prompt,
            tools=tools,
            on_tool_use_start=on_tool_use_start,
            on_tool_use_args_delta=on_tool_use_args_delta,
            on_tool_use=on_tool_use,
            web_search=self.get_setting("web_search"),
        )

    def __complete_chat(self):
        if self.__is_generating:
            return

        self.__is_generating = True

        message = Message(
            role="assistant",
            text="",
            timestamp=datetime.now().timestamp(),
        )
        self.get_messages().append(message)

        def complete() -> Tuple[Optional[str], bool]:
            message["text"] = ""
            msg_index = len(self.get_messages()) - 1
            line: Optional[Line] = None
            subindex = 0
            self.process_events(raise_keyboard_interrupt=True)
            try:
                for chunk in self.complete_chat(
                    self.get_messages(),
                    model=self.get_setting("model"),
                    system_prompt=self.get_system_prompt(),
                ):
                    message["text"] += chunk
                    for i, a in enumerate(chunk.split("\n")):
                        if i > 0 or line is None:
                            line = Line(
                                role="assistant",
                                msg_index=msg_index,
                                subindex=subindex,
                            )
                            subindex += 1
                            self.append_item(line)
                        line.text += a

                    self.update_screen()
                    self.process_events(raise_keyboard_interrupt=True)
                return message["text"], False
            except KeyboardInterrupt:
                message["text"] += f"\n{_INTERRUPT_MESSAGE}"
                self.append_item(
                    Line(
                        role="assistant",
                        text=f"{_INTERRUPT_MESSAGE}",
                        msg_index=msg_index,
                        subindex=subindex,
                    )
                )
                return message["text"], True

        text_content = None
        while text_content is None:  # retry on exception
            try:
                text_content, interrupted = complete()
            except Exception:
                ExceptionMenu().exec()

        self.__is_generating = False
        self.save_chat()
        # self.__refresh_lines()

        if not interrupted:
            self.on_message(text_content)

            if self.__copy:
                set_clip(text_content)
                self.close()
            elif self.__out_file:
                with open(self.__out_file, "w", encoding="utf-8") as f:
                    f.write(text_content)
                self.close()

        while not self.__after_chat_completion.empty():
            (self.__after_chat_completion.get())()

    def save_chat(self):
        if self.__chat_file is None:
            return
        os.makedirs(os.path.dirname(self.__chat_file), exist_ok=True)
        save_json(self.__chat_file, self.__messages)
        self.__history_manager.delete_old_files()
        self.set_message(f"Chat saved to {self.__chat_file}")

    def __refresh_lines(self):
        self.__lines[:] = []
        for msg_index, message in enumerate(self.get_messages()):
            subindex = 0

            # Text content
            if message["text"]:
                for line in message["text"].splitlines():
                    self.__lines.append(
                        Line(
                            role=message["role"],
                            text=line,
                            msg_index=msg_index,
                            subindex=subindex,
                        )
                    )
                    subindex += 1

            # Image file
            image_file = message.get("image_file", None)
            if image_file:
                self.__lines.append(
                    Line(
                        role=message["role"],
                        text=f"* Image: {image_file}",
                        msg_index=msg_index,
                        subindex=subindex,
                    )
                )
                subindex += 1

            # Tool uses
            for tool_use in message.get("tool_use", []):
                self.__lines.append(
                    Line(
                        role=message["role"],
                        msg_index=msg_index,
                        subindex=subindex,
                        tool_use=tool_use,
                    )
                )
                subindex += 1

            # Tool results
            for tool_result in message.get("tool_result", []):
                self.__lines.append(
                    Line(
                        role=message["role"],
                        msg_index=msg_index,
                        subindex=subindex,
                        tool_result=tool_result,
                    )
                )
                subindex += 1

        self.update_screen()

    def load_chat(self, file: Optional[str] = None):
        if file is not None:
            self.__chat_file = file

        if not self.__chat_file:
            return

        if not os.path.exists(self.__chat_file):
            self.set_message(f"Conv file not exist: {self.__chat_file}")
            return

        self.__messages = load_json(self.__chat_file)
        self.__refresh_lines()

    def clear_messages(self):
        self.__lines.clear()
        self.get_messages().clear()
        token_count.reset()
        self.reset_selection()
        self.set_follow(True)
        self.update_screen()

    def new_chat(self, message: Optional[str] = None):
        self.clear_messages()

        if self.__auto_create_chat_file:
            self.__chat_file = self.__history_manager.get_new_file()

        if message:
            self.send_message(message)
        else:
            self.update_screen()

    def on_enter_pressed(self):
        try:
            self.__cancel_chat_completion()
            self.send_message(self.get_input())
        except KeyboardInterrupt:
            self.__after_chat_completion.put(
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

    def get_system_prompt(self) -> str:
        return self.__system_prompt

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
                    self.__attachment = temp_file.name
                    self.__update_prompt()
                    return True

        return False


def _main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=str, nargs="?", help="input message")
    parser.add_argument("-a", "--attachment", type=str, nargs="?")
    parser.add_argument("-i", "--in-file", type=str)
    parser.add_argument("-o", "--out-file", type=str)
    parser.add_argument("-m", "--model", type=str)
    parser.add_argument("--edit-text", action="store_true")
    parser.add_argument("--copy", action="store_true")
    args = parser.parse_args()

    if args.in_file:
        with open(args.in_file, "r", encoding="utf-8") as f:
            message = f.read()
    elif not sys.stdin.isatty():
        message = sys.stdin.read()
    else:
        message = args.input

    chat = ChatMenu(
        message=message,
        attachment=args.attachment,
        out_file=args.out_file,
        model=args.model,
        edit_text=args.edit_text,
        copy=args.copy,
    )
    chat.exec()


if __name__ == "__main__":
    _main()
