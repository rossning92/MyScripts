import argparse
import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import ML.gpt.chat_menu
from ai.chat import get_tool_use_text
from ai.tool_use import (
    ToolResult,
    ToolUse,
    get_tool_use_prompt,
    parse_text_for_tool_use,
)
from ML.gpt.chat_menu import ChatMenu, Line
from utils.jsonutil import load_json, save_json
from utils.menu.confirmmenu import ConfirmMenu
from utils.menu.filemenu import FileMenu
from utils.menu.inputmenu import InputMenu
from utils.strutil import to_ordinal
from utils.template import render_template

MODULE_NAME = Path(__file__).stem
DATA_DIR = os.path.join(".config", MODULE_NAME)
AGENT_FILE = "agent.json"
AGENT_DEFAULT = {
    "task": "",
    "agents": [],
    "context": {},
}


def _get_prompt(tools: Optional[List[Callable]] = None):
    prompt = """You are my assistant to help me complete a task.
- Once the task is complete, your reply must be enclosed in <result> and </result> to indicate the task is finished.
- You should do what the user asks you to do, and nothing else.

# Tone

- You should be concise, direct, and to the point.
- You should answer the user's question directly without elaboration, explanation, or details, unless the user asks for them.
- You should keep your response to 1-2 sentences (not including tool use or code generation).
- You should NOT answer with unnecessary preamble or postamble (such as explaining your code or summarizing your action), unless the user asks you to.

# Code style

- Do NOT add comments to code unless the user requests it or the code is complex and needs context.
- You should follow existing code style, conventions, and utilize available libraries and utilities.
"""

    if tools:
        prompt += "\n" + get_tool_use_prompt(tools)

    return prompt


class SettingsMenu(ML.gpt.chat_menu.SettingsMenu):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_default_values(self) -> Dict[str, Any]:
        return {
            **super().get_default_values(),
            "tool_use_api": True,
        }


class AgentMenu(ChatMenu):
    def __init__(
        self,
        context: Optional[Dict] = None,
        agent_file: Optional[str] = None,
        yes_always=True,
        run=False,
        load_last_agent=False,
        data_dir: str = DATA_DIR,
        settings_menu_class=SettingsMenu,
        **kwargs,
    ):
        self.__agent = AGENT_DEFAULT.copy()
        self.__agent_file = agent_file or os.path.join(data_dir, AGENT_FILE)
        self.__data_dir = data_dir
        self.__run = run
        self.__tools = self.get_tool_list()
        self.__yes_always = yes_always

        super().__init__(
            data_dir=data_dir,
            chat_file=os.path.join(self.__data_dir, "chat.json"),
            settings_menu_class=settings_menu_class,
            **kwargs,
        )

        os.makedirs(data_dir, exist_ok=True)

        if agent_file:
            self.__load_agent(agent_file, context=context)
        else:
            if load_last_agent:
                self.__load_agent()
            else:
                self.__new_agent()

        self.task_result: Optional[str] = None

        self.add_command(self.__edit_context, hotkey="alt+c")
        self.add_command(self.__load_agent, hotkey="alt+l")
        self.add_command(self.__new_agent, hotkey="ctrl+n")
        self.add_command(self.__open_file_menu, hotkey="alt+f")

    def __edit_context(self):
        assert isinstance(self.__agent["context"], dict)
        self.__agent["context"].clear()
        self.__get_task_with_context()

    def __load_agent(
        self,
        agent_file: Optional[str] = None,
        clear_messages=False,
        context: Optional[Dict] = None,
    ):
        if agent_file is not None:
            self.__agent_file = agent_file

        if clear_messages:
            self.__agent = AGENT_DEFAULT.copy()
        else:
            self.__agent = load_json(
                self.__agent_file,
                default=AGENT_DEFAULT.copy(),
            )

        if context:
            assert isinstance(self.__agent["context"], dict)
            self.__agent["context"].update(context)

        self.load_chat()

    def __new_agent(self):
        self.__agent_file = os.path.join(self.__data_dir, AGENT_FILE)
        self.__agent = AGENT_DEFAULT.copy()
        self.new_chat()

    def on_created(self):
        if self.__run:
            self.send_message(self.get_prompt())

    def on_message(self, content: str):
        self.__handle_response()

    def send_message(
        self,
        text: str,
        tool_results: Optional[List[ToolResult]] = None,
    ) -> None:
        if len(self.get_messages()) == 0:
            self.__agent["task"] = text
            self.__save_agent()

        return super().send_message(text, tool_results)

    def __save_agent(self):
        os.makedirs(os.path.dirname(self.__agent_file), exist_ok=True)
        save_json(self.__agent_file, self.__agent)

    def __get_task_with_context(self):
        while True:
            undefined_names: List[str] = []
            task = render_template(
                template=self.__agent["task"],
                context=self.__agent["context"],
                undefined_names=undefined_names,
            )
            if len(undefined_names) > 0:
                for name in undefined_names:
                    val = InputMenu(prompt=name).request_input()
                    if val:
                        assert isinstance(self.__agent["context"], dict)
                        self.__agent["context"][name] = val
                        self.__save_agent()
            else:
                return task

    def get_prompt(self) -> str:
        return self.__get_task_with_context()

    def get_tool_list(self) -> List[Callable]:
        tools: List[Callable] = []

        for agent_name in self.__agent["agents"]:
            if not isinstance(agent_name, str):
                raise Exception('Invalid value in "agents"')

            # Get input parameters for the agent
            agent_file = os.path.join(
                os.path.dirname(self.__agent_file), agent_name + ".json"
            )
            agent = load_json(agent_file)
            params: List[str] = []  # function parameter names
            render_template(
                template=agent["task"],
                undefined_names=params,
                context=self.__agent["context"],
            )
            signature = "(" + ", ".join([f"{p}: str" for p in params]) + ")"

            # Convert agent as a tool that can be called through a Python function call.
            def exec_agent(context):
                menu = AgentMenu(
                    context=context,
                    agent_file=agent_file,
                    yes_always=self.__yes_always,
                    run=True,
                )
                menu.exec()
                return menu.task_result

            scope = {"exec_agent": exec_agent}
            exec(
                f"def {agent_name}{signature}: return exec_agent(context=locals())",
                scope,
            )
            tools.append(scope[agent_name])
        return tools

    def get_tools(self) -> Optional[List[Callable[..., Any]]]:
        return self.get_tool_list() if self.get_setting("tool_use_api") else None

    def get_system_prompt(self) -> str:
        return (
            _get_prompt()
            if self.get_setting("tool_use_api")
            else _get_prompt(tools=self.__tools)
        )

    def __handle_response(self):
        messages = self.get_messages()
        if len(messages) <= 0:
            return

        last_message = messages[-1]
        text_content = last_message["text"]

        reply = ""
        interrupted = False
        has_error = False

        tool_uses = (
            (last_message["tool_use"].copy() if "tool_use" in last_message else [])
            if self.get_setting("tool_use_api")
            else list(parse_text_for_tool_use(text_content, self.__tools))
        )

        tool_results: List[ToolResult] = []
        for i, tool_use in enumerate(tool_uses):
            tool = next(
                tool for tool in self.__tools if tool.__name__ == tool_use["tool_name"]
            )

            # Run tool
            if not self.__yes_always:
                menu = ConfirmMenu(f"Run tool ({tool_use['tool_name']})?")
                menu.exec()
                if menu.is_confirmed():
                    should_run = True
                else:
                    should_run = False
                    if self.get_setting("tool_use_api"):
                        tool_results.append(
                            ToolResult(
                                tool_use_id=tool_use["tool_use_id"],
                                content="Tool was interrupted by user.",
                            )
                        )
                    else:
                        reply += f"The {to_ordinal(i+1)} tool ({tool_use['tool_name']}) was interrupted by user.\n"
                    break
            else:
                should_run = True

            if should_run:
                try:
                    ret = tool(**tool_use["args"])
                    if ret:
                        if self.get_setting("tool_use_api"):
                            tool_results.append(
                                ToolResult(
                                    tool_use_id=tool_use["tool_use_id"],
                                    content=str(ret),
                                )
                            )
                        else:
                            reply += f"""The {to_ordinal(i+1)} tool ({tool_use['tool_name']}) returned:
-------
{str(ret)}
-------

"""

                    else:
                        if self.get_setting("tool_use_api"):
                            tool_results.append(
                                ToolResult(
                                    tool_use_id=tool_use["tool_use_id"],
                                    content="Tool completed successfully.",
                                )
                            )
                        else:
                            reply += f"The {to_ordinal(i+1)} tool ({tool_use['tool_name']}) completed successfully.\n\n"

                except Exception as ex:
                    has_error = True
                    if self.get_setting("tool_use_api"):
                        tool_results.append(
                            ToolResult(
                                tool_use_id=tool_use["tool_use_id"],
                                content=str(ex),
                            )
                        )
                    else:
                        reply += f"""ERROR in the {to_ordinal(i+1)} tool ({tool_use['tool_name']}):
-------
{str(ex)}
-------

"""
                except KeyboardInterrupt:
                    interrupted = True
                    if self.get_setting("tool_use_api"):
                        tool_results.append(
                            ToolResult(
                                tool_use_id=tool_use["tool_use_id"],
                                content="Tool was interrupted by user.",
                            )
                        )
                    else:
                        reply += f"The {to_ordinal(i+1)} tool using {tool_use['tool_name']} was interrupted by user.\n"
                    break

        # Check if the task is completed
        result = re.findall(
            r"<result>\s*([\S\s]*?)\s*</result>", text_content, flags=re.MULTILINE
        )
        if len(result) > 0:
            self.task_result = result[0] if result[0] else "Returns nothing."
            if self.__run:
                self.close()

            self.on_response(result[0], done=True)
            self.on_result(result[0])

        elif not reply:
            self.on_response(text_content, done=False)

        reply = reply.rstrip()
        if reply or tool_results:
            if not has_error and (result or interrupted):
                self.append_user_message(reply, tool_results=tool_results)
            else:
                self.send_message(reply, tool_results=tool_results)

    def on_response(self, text: str, done: bool):
        pass

    def on_result(self, result: str):
        pass

    def __get_next_message_index_and_subindex(self):
        msg_index = len(self.get_messages()) - 1
        if len(self.items) > 0 and self.items[-1].msg_index == msg_index:
            subindex = self.items[-1].subindex + 1
        else:
            subindex = 0
        return msg_index, subindex

    def on_tool_use_start(self, tool_use: ToolUse):
        if not self.get_setting("tool_use_api"):
            return

        msg_index, subindex = self.__get_next_message_index_and_subindex()
        self.append_item(
            Line(
                role="assistant",
                text=get_tool_use_text(tool_use),
                msg_index=msg_index,
                subindex=subindex,
                tool_use=tool_use,
            )
        )
        self.process_events()

    def on_tool_use_args_delta(self, text: str):
        if not self.get_setting("tool_use_api"):
            return

    def on_tool_use(self, tool_use: ToolUse):
        if not self.get_setting("tool_use_api"):
            return

        messages = self.get_messages()
        assert len(messages) > 0
        if "tool_use" not in messages[-1]:
            messages[-1]["tool_use"] = []
        messages[-1]["tool_use"].append(tool_use)

        # Add or update tool use result
        exists = False
        for line in reversed(self.items):
            if (
                line.tool_use
                and line.tool_use["tool_use_id"] == tool_use["tool_use_id"]
            ):
                line.tool_use = tool_use
                exists = True
                break
        if not exists:
            msg_index, subindex = self.__get_next_message_index_and_subindex()
            self.append_item(
                Line(
                    role="assistant",
                    text=get_tool_use_text(tool_use),
                    msg_index=msg_index,
                    subindex=subindex,
                    tool_use=tool_use,
                )
            )

    def __open_file_menu(self):
        FileMenu(goto=os.getcwd()).exec()

    def get_status_text(self) -> str:
        tools = "|".join([tool.__name__ for tool in self.__tools])
        s = f"TOOLS: {tools}\nCWD  : {os.getcwd()}"
        return s + "\n" + super().get_status_text()

    def get_data_dir(self) -> str:
        return self.__data_dir


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--agent",
        type=str,
    )
    parser.add_argument(
        "-c",
        "--context",
        metavar="KEY=VALUE",
        nargs="+",
    )
    parser.add_argument(
        "-r",
        "--run",
        action="store_true",
    )

    args = parser.parse_args()
    context = dict(kvp.split("=") for kvp in args.context) if args.context else None

    menu = AgentMenu(
        context=context,
        agent_file=args.agent,
        run=args.run,
    )
    menu.exec()


if __name__ == "__main__":
    _main()
