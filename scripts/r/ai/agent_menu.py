import functools
import glob
import os
import shlex
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypedDict, cast

import ai.chat_menu
import ai.tools.bash
import ai.tools.edit
import ai.tools.glob
import ai.tools.grep
import ai.tools.list
import ai.tools.read
from ai.chat import get_tool_use_text
from ai.chat_menu import ChatMenu, Line
from ai.mcp import MCPClient
from ai.skill import get_skill_prompt, get_skills
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


def _get_prompt(
    tools: Optional[List[ToolDefinition]] = None,
    skill: bool = False,
) -> str:
    prompt = ""

    if tools:
        prompt += "\n" + get_tool_use_prompt(tools)

    if skill:
        skill_prompt = get_skill_prompt()
        if skill_prompt:
            prompt += "\n" + skill_prompt

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
            "enable_tools": True,
            "function_call": True,
            "mcp": [],
            "skill": False,
        }

    def get_schema(self) -> Optional[JSONSchema]:
        schema = super().get_schema()
        assert schema and schema["type"] == "object"
        schema["properties"]["enable_tools"] = {"type": "boolean"}
        schema["properties"]["function_call"] = {"type": "boolean"}
        schema["properties"]["mcp"] = {
            "type": "array",
            "items": {"type": "object", "properties": {"command": {"type": "string"}}},
        }
        schema["properties"]["skill"] = {"type": "boolean"}
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
        settings_menu_class=SettingsMenu,
        mcp: Optional[List[_MCP]] = None,
        subagents: Optional[List[_Subagent]] = None,
        tools_callable: Optional[List[Callable]] = None,
        **kwargs,
    ):
        self.__yes_always = yes_always
        self.__subagents = subagents if subagents else []

        super().__init__(
            settings_menu_class=settings_menu_class,
            **kwargs,
        )

        mcp_items = mcp if mcp else cast(List[_MCP], self.get_settings()["mcp"])
        self.__mcp_clients = [
            MCPClient(command=shlex.split(item["command"])) for item in mcp_items
        ]

        self.add_command(self.__open_file_menu, hotkey="alt+f")
        self.add_command(self.__toggle_tools, hotkey="ctrl+t")

        self.__tools_callable = (
            tools_callable
            if tools_callable is not None
            else [
                self.__hook_read_tool(ai.tools.read.read)
                if self.get_settings()["skill"]
                else ai.tools.read.read,
                ai.tools.edit.edit,
                ai.tools.bash.bash,
                ai.tools.list.list,
                ai.tools.glob.glob,
                ai.tools.grep.grep,
            ]
        )

        self.__update_tools()

    def __update_tools(self):
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
        if not self.get_settings()["enable_tools"]:
            return []

        return (
            [function_to_tool_definition(t) for t in self.get_tools_callable()]
            + self.__get_tools_subagent()
            + [t for client in self.__mcp_clients for t in client.list_tools()]
        )

    def get_system_prompt(self) -> str:
        return _get_prompt(
            tools=None if self.get_settings()["function_call"] else self.__tools,
            skill=self.get_settings()["skill"],
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
            if self.get_settings()["function_call"]
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
                    if self.get_settings()["function_call"]:
                        tool_results.append(
                            ToolResult(
                                tool_use_id=tool_use["tool_use_id"],
                                content="Tool was interrupted by user.",
                            )
                        )
                    else:
                        reply += f"The {to_ordinal(i + 1)} tool ({tool_use['tool_name']}) was interrupted by user.\n"
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
                        if self.get_settings()["function_call"]:
                            tool_results.append(
                                ToolResult(
                                    tool_use_id=tool_use["tool_use_id"],
                                    content=str(ret),
                                )
                            )
                        else:
                            reply += f"""The {to_ordinal(i + 1)} tool ({tool_use["tool_name"]}) returned:
-------
{str(ret)}
-------

"""

                    else:
                        if self.get_settings()["function_call"]:
                            tool_results.append(
                                ToolResult(
                                    tool_use_id=tool_use["tool_use_id"],
                                    content="Tool completed successfully.",
                                )
                            )
                        else:
                            reply += f"The {to_ordinal(i + 1)} tool ({tool_use['tool_name']}) completed successfully.\n\n"

                except Exception as ex:
                    has_error = True
                    if self.get_settings()["function_call"]:
                        tool_results.append(
                            ToolResult(
                                tool_use_id=tool_use["tool_use_id"],
                                content=str(ex),
                            )
                        )
                    else:
                        reply += f"""ERROR in the {to_ordinal(i + 1)} tool ({tool_use["tool_name"]}):
-------
{str(ex)}
-------

"""
                except KeyboardInterrupt:
                    interrupted = True
                    if self.get_settings()["function_call"]:
                        tool_results.append(
                            ToolResult(
                                tool_use_id=tool_use["tool_use_id"],
                                content="Tool was interrupted by user.",
                            )
                        )
                    else:
                        reply += f"The {to_ordinal(i + 1)} tool using {tool_use['tool_name']} was interrupted by user.\n"
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
        if not self.get_settings()["function_call"]:
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
        if not self.get_settings()["function_call"]:
            return

    def on_tool_use(self, tool_use: ToolUse):
        if not self.get_settings()["function_call"]:
            return

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

    def __toggle_tools(self):
        enabled = not self.get_settings()["enable_tools"]
        self.set_setting("enable_tools", enabled)
        self.__update_tools()
        self.set_message(f"Tools {'on' if enabled else 'off'}")

    def __open_file_menu(self):
        FileMenu(goto=os.getcwd()).exec()

    def get_status_text(self) -> str:
        s = f"cwd={os.getcwd()}"

        if self.__tools:
            s += "  tools=" + "|".join([tool.name for tool in self.__tools])

        return s + "\n" + super().get_status_text()

    def on_close(self):
        for c in self.__mcp_clients:
            c.close()
        super().on_close()

    def __hook_read_tool(self, func):
        @functools.wraps(func)
        def wrapper(file: str, **kwargs) -> str:
            if skill := next((s for s in get_skills() if s.file_path == file), None):
                self.__mcp_clients.extend(
                    MCPClient(command=shlex.split(c))
                    for c in skill.metadata.get("mcp_servers", [])
                )
                self.__update_tools()
                return skill.content
            return func(file=file, **kwargs)

        return wrapper


def _main():
    menu = AgentMenu(data_dir=DATA_DIR)
    menu.exec()


if __name__ == "__main__":
    _main()
