import argparse
import difflib
import os
from pathlib import Path
from platform import platform
from typing import Any, Dict, List, Optional

import ai.agent_menu
from ai.agent_menu import AgentMenu, load_subagents
from ai.chat_menu import Line
from ai.filecontextmenu import FileContextMenu
from ai.message import Message
from ai.tool_use import ToolUse
from ai.tools import Settings
from utils.checkpoints import (
    get_oldest_files_since_timestamp,
    restore_files_since_timestamp,
)
from utils.editor import edit_text_file
from utils.menu.diffmenu import DiffMenu
from utils.menu.filemenu import FileMenu

_SYSTEM_PROMPT = """You are my assistant to help me complete a task.

# Tone

- You should be concise, direct, and to the point.
- You should answer the user's question directly without elaboration, explanation, or details, unless the user asks for them.
- You should keep your response to 1-2 sentences (not including tool use or code generation).
- You should NOT answer with unnecessary preamble or postamble (such as explaining your code or summarizing your action), unless the user asks you to.

# Code style

- Do NOT add comments to code unless the user requests it or the code is complex and needs context.
- You should follow existing code style, conventions, and utilize available libraries and utilities.
"""

_RULE_FILE = "AGENTS.md"


def _get_env_info() -> str:
    return f"""# Environment Information

Platform: {platform()}
Working directory: {os.getcwd()}
"""


class SettingsMenu(ai.agent_menu.SettingsMenu):
    # default_model = "gpt-5.2(medium)"
    default_model = "gemini-3-flash-preview"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__update_settings()

    def get_default_values(self) -> Dict[str, Any]:
        return {
            **super().get_default_values(),
            "model": SettingsMenu.default_model,
            "need_confirm": True,
            "auto_open_diff": False,
        }

    def on_dict_update(self, data):
        super().on_dict_update(data)
        self.__update_settings()

    def __update_settings(self):
        Settings.need_confirm = self.data["need_confirm"]


class CodeAgentMenu(AgentMenu):
    def __init__(
        self,
        files: Optional[List[str]],
        settings_menu_class=SettingsMenu,
        **kwargs,
    ):
        super().__init__(
            data_dir=os.path.join(".config", "coder"),
            settings_menu_class=settings_menu_class,
            subagents=load_subagents(),
            **kwargs,
        )
        self.__file_context_menu = FileContextMenu(files=files)
        self.add_command(self.__add_file, hotkey="@")
        self.add_command(self.__edit_instructions)
        self.add_command(self.__open_diff, hotkey="ctrl+d")

    def __edit_instructions(self):
        self.call_func_without_curses(
            lambda: edit_text_file(os.path.join(self.get_data_dir(), _RULE_FILE))
        )

    def __get_rules(self) -> str:
        file = os.path.join(self.get_data_dir(), _RULE_FILE)
        if not os.path.exists(file):
            return ""

        with open(file, "r", encoding="utf-8") as f:
            s = f.read().strip()
        if not s:
            return ""

        return f"""# General Instructions

{s}
"""

    def __open_diff(self):
        messages = self.get_messages()
        if len(messages) == 0:
            self.set_message("No messages found")
            return

        for history_dir, rel_path in get_oldest_files_since_timestamp(
            messages[0]["timestamp"]
        ):
            DiffMenu(file1=os.path.join(history_dir, rel_path), file2=rel_path).exec()

    def get_system_prompt(self) -> str:
        prompt_parts = [_SYSTEM_PROMPT]

        system = super().get_system_prompt()
        if system:
            prompt_parts.append(system)

        rules = self.__get_rules()
        if rules:
            prompt_parts.append(rules)

        file_context = self.__file_context_menu.get_prompt()
        if file_context:
            prompt_parts.append(file_context)

        env = _get_env_info()
        if env:
            prompt_parts.append(env)

        return "\n".join(prompt_parts)

    def revert_messages(self, from_msg_index: int) -> List[Message]:
        removed_messages = super().revert_messages(from_msg_index=from_msg_index)
        for message in reversed(removed_messages):
            restore_files_since_timestamp(timestamp=message["timestamp"])
        return removed_messages

    def get_status_text(self) -> str:
        status_lines = []
        files = self.__file_context_menu.get_status_text()
        if files:
            status_lines.append(files)
        status_lines.append(super().get_status_text())
        return "\n".join(status_lines)

    def __add_file(self):
        file_menu = FileMenu()
        file = file_menu.select_file()
        if file:
            cwd = os.getcwd()
            if os.path.commonpath([cwd, file]) == cwd:
                path = os.path.relpath(file, cwd)
            else:
                path = file
            self.insert_text(f"`{path}` ")

    def on_result(self, result: str):
        if self.get_settings()["auto_open_diff"]:
            self.__open_diff()

    def _get_tool_use_lines(
        self, tool_use: ToolUse, msg_index: int, subindex: int
    ) -> List[Line]:
        lines = super()._get_tool_use_lines(tool_use, msg_index, subindex)
        if tool_use["tool_name"] == "edit":
            lines.extend(
                self.__get_edit_diff_lines(tool_use, msg_index, subindex + len(lines))
            )
        return lines

    def on_tool_use(self, tool_use: ToolUse):
        super().on_tool_use(tool_use)
        if tool_use["tool_name"] == "edit":
            msg_index, subindex = self.get_message_index_and_subindex()
            for line in self.__get_edit_diff_lines(tool_use, msg_index, subindex):
                self.append_item(line)

    def __get_edit_diff_lines(
        self, tool_use: ToolUse, msg_index: int, subindex: int
    ) -> List[Line]:
        old_string = tool_use["args"].get("old_string", "")
        new_string = tool_use["args"].get("new_string", "")

        class IgnoreLeadingWhitespaceLine(str):
            def __eq__(self, other):
                return self.lstrip() == other.lstrip()

            def __hash__(self):
                return hash(self.lstrip())

        diff = difflib.unified_diff(
            [IgnoreLeadingWhitespaceLine(line) for line in old_string.splitlines()],
            [IgnoreLeadingWhitespaceLine(line) for line in new_string.splitlines()],
            n=1,
            lineterm="",
        )
        lines = []
        for line in diff:
            if line.startswith(("---", "+++", "@@")):
                continue
            lines.append(
                Line(
                    role="assistant",
                    text=line,
                    msg_index=msg_index,
                    subindex=subindex,
                )
            )
            subindex += 1
        return lines

    def get_item_color(self, item: Line) -> str:
        if item.role == "assistant":
            if item.text.startswith("+"):
                return "green"
            elif item.text.startswith("-"):
                return "red"
        return super().get_item_color(item)


def _find_git_root(path) -> Optional[str]:
    current = Path(path)
    while current != current.parent:
        if (current / ".git").exists():
            return str(current)
        current = current.parent
    return None


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*")
    parser.add_argument(
        "-d",
        "--repo-path",
        "--dir",
        dest="repo_path",
        type=str,
        default=os.environ.get("REPO_PATH"),
    )
    parser.add_argument("-m", "--model", type=str)
    args = parser.parse_args()

    if args.model:
        SettingsMenu.default_model = args.model

    # Change directory to the project root
    if len(args.files) == 1 and os.path.isabs(args.files[0]):
        root = os.path.dirname(args.files[0])
        git_root = _find_git_root(root)
        if git_root:
            root = git_root
    elif args.repo_path:
        if not os.path.exists(args.repo_path):
            os.makedirs(args.repo_path, exist_ok=True)
        root = args.repo_path
    else:
        git_root = _find_git_root(os.getcwd())
        if git_root:
            root = git_root
        else:
            root = os.getcwd()
    os.chdir(root)

    # Convert files to relative path
    files = [
        os.path.relpath(file, root) if os.path.isabs(file) else file
        for file in args.files
    ]

    menu = CodeAgentMenu(files=files)
    menu.exec()


if __name__ == "__main__":
    _main()
