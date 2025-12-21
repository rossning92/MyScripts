import glob
import os
import shlex
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypedDict, cast

import ai.chat_menu
from ai.chat import get_tool_use_text
from ai.chat_menu import ChatMenu, Line
from ai.mcp import MCPClient
from ai.tool_use import (
    ToolDefinition,
    ToolParam,
    ToolResult,
    ToolUse,
    function_to_tool_definition,
    get_tool_use_prompt,
    parse_text_for_tool_use,
)
from utils.jsonschema import JSONSchema
from utils.jsonutil import load_json
from utils.menu.confirmmenu import ConfirmMenu
from utils.menu.filemenu import FileMenu
from utils.strutil import to_ordinal

MODULE_NAME = Path(__file__).stem
DATA_DIR = os.path.join(".config", MODULE_NAME)


def _get_prompt(tools: Optional[List[ToolDefinition]] = None) -> str:
    prompt = """You are my assistant to help me complete a task.

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


class _MCP(TypedDict):
    command: str


class _Subagent(TypedDict):
    name: str
    description: str
    system_prompt: str


class SettingsMenu(ai.chat_menu.SettingsMenu):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_default_values(self) -> Dict[str, Any]:
        return {
            **super().get_default_values(),
            "tool_use_api": True,
            "mcp": [],
        }

    def get_schema(self) -> Optional[JSONSchema]:
        schema = super().get_schema()
        assert schema and schema["type"] == "object"
        schema["properties"]["tool_use_api"] = {"type": "boolean"}
        schema["properties"]["mcp"] = {
            "type": "array",
            "items": {"type": "object", "properties": {"command": {"type": "string"}}},
        }
        return schema


def load_subagents() -> List[_Subagent]:
    script_dir = Path(__file__).parent
    subagents_dir = script_dir / "subagents"
    subagents: List[_Subagent] = []

    for json_file in glob.glob(str(subagents_dir / "*.json")):
        subagent: _Subagent = load_json(json_file)
        agent_name = Path(json_file).stem
        subagent["name"] = agent_name
        subagents.append(subagent)
    return subagents


class AgentMenu(ChatMenu):
    def __init__(
        self,
        yes_always=True,
        data_dir: str = DATA_DIR,
        settings_menu_class=SettingsMenu,
        mcp: Optional[List[_MCP]] = None,
        subagents: Optional[List[_Subagent]] = None,
        tools_callable: Optional[List[Callable]] = None,
        **kwargs,
    ):
        self.__data_dir = data_dir
        self.__yes_always = yes_always
        self.__subagents = subagents if subagents else []
        self.__tools_callable = tools_callable if tools_callable is not None else []

        super().__init__(
            data_dir=data_dir,
            settings_menu_class=settings_menu_class,
            **kwargs,
        )

        mcp_items = mcp if mcp else cast(List[_MCP], self.get_setting("mcp"))
        self.__mcp_clients = [
            MCPClient(command=shlex.split(item["command"])) for item in mcp_items
        ]

        os.makedirs(data_dir, exist_ok=True)

        self.add_command(self.__open_file_menu, hotkey="alt+f")

        self.__tools = self.get_tools()

    def on_message(self, content: str):
        self.__handle_response()

    def __get_tools_subagent(self) -> List[ToolDefinition]:
        subagents = self.__subagents
        return [
            ToolDefinition(
                name=subagent["name"],
                description=subagent["description"],
                parameters=[
                    ToolParam(
                        name="prompt",
                        type={"type": "string"},
                        description="The task for the agent to perform",
                    ),
                ],
                required=["prompt"],
            )
            for subagent in subagents
        ]

    def get_tools_callable(self) -> List[Callable]:
        return self.__tools_callable

    def get_tools(self) -> List[ToolDefinition]:
        return (
            (
                [function_to_tool_definition(t) for t in self.get_tools_callable()]
                + self.__get_tools_subagent()
                + [t for client in self.__mcp_clients for t in client.list_tools()]
            )
            if self.get_setting("tool_use_api")
            else []
        )

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
                    tool_name = tool_use["tool_name"]
                    tool = next(
                        (
                            t
                            for t in self.get_tools_callable()
                            if t.__name__ == tool_name
                        ),
                        None,
                    )
                    if tool:  # Call function tool
                        ret = tool(**tool_use["args"])

                    else:  # Call MCP tool
                        client = next(
                            (
                                c
                                for c in self.__mcp_clients
                                if any(
                                    t.name == tool_use["tool_name"]
                                    for t in c.list_tools()
                                )
                            ),
                            None,
                        )
                        if client:
                            ret = client.call_tool(tool_use)
                        else:
                            subagent = next(
                                a for a in self.__subagents if a["name"] == tool_name
                            )
                            menu = AgentMenu(
                                system_prompt=subagent["system_prompt"],
                                prompt=f"subagent={tool_name}",
                                message=tool_use["args"]["prompt"],
                                tools_callable=self.get_tools_callable(),
                                yes_always=self.__yes_always,
                                cancellable=True,
                            )
                            menu.exec()
                            ret = menu.get_messages()[-1]["text"]

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

        if not reply:
            self.on_response(text_content, done=not reply and not tool_results)

        reply = reply.rstrip()
        if reply or tool_results:
            if not has_error and interrupted:
                self.append_user_message(reply, tool_results=tool_results)
            else:
                self.send_message(reply, tool_results=tool_results)

    def on_response(self, text: str, done: bool):
        pass

    def on_tool_use_start(self, tool_use: ToolUse):
        if not self.get_setting("tool_use_api"):
            return

        msg_index, subindex = self.get_message_index_and_subindex()
        self.append_item(
            Line(
                role="assistant",
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

        assert self._out_message
        if "tool_use" not in self._out_message:
            self._out_message["tool_use"] = []
        self._out_message["tool_use"].append(tool_use)

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
            msg_index, subindex = self.get_message_index_and_subindex()
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
        s = f"cwd={os.getcwd()}"

        if self.__tools:
            s += "  tools=" + "|".join([tool.name for tool in self.__tools])

        return s + "\n" + super().get_status_text()

    def get_data_dir(self) -> str:
        return self.__data_dir

    def on_close(self):
        for c in self.__mcp_clients:
            c.close()
        super().on_close()


def _main():
    menu = AgentMenu()
    menu.exec()


if __name__ == "__main__":
    _main()
