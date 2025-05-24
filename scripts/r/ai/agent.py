import argparse
import glob
import inspect
import logging
import os
import re
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from ai.toolutil import get_all_tools, load_tool
from ML.gpt.chatmenu import ChatMenu
from utils.editor import edit_text
from utils.jsonutil import load_json, save_json
from utils.menu import Menu
from utils.menu.confirmmenu import ConfirmMenu
from utils.menu.filemenu import FileMenu
from utils.menu.inputmenu import InputMenu
from utils.template import render_template

SETTING_DIR = "tmp"
MODULE_NAME = Path(__file__).stem
CHAT_DIR = os.path.join(SETTING_DIR, MODULE_NAME + "_chats")
AGENT_DIR = os.path.join(SETTING_DIR, MODULE_NAME + "_agents")
UNSAVED_AGENT_FILE = "unsaved.json"


def _find_xml_strings(tags: List[str], s: str) -> List[str]:
    tag_patt = "(?:" + "|".join([re.escape(tag) for tag in tags]) + ")"
    return re.findall(rf"<{tag_patt}>[\S\s]*?</{tag_patt}>", s, flags=re.MULTILINE)


def _parse_xml_string_for_tool(s: str) -> Tuple[str, Dict[str, str]]:
    match = re.match(r"^\s*<([a-z_]+)>([\d\D]*?)</\1>\s*$", s)
    if match is None:
        raise Exception()
    tool_name = match.group(1)
    params_xml_str = match.group(2)

    param_patt = re.compile(r"^\s*<([a-z_]+)>[\r\n]*([\d\D]*?)[\r\n]*</\1>\s*")
    params: Dict[str, str] = {}
    while True:
        match = re.match(param_patt, params_xml_str)
        if match:
            name = match.group(1)
            if name in params:
                raise ValueError(f"Duplicate parameter detected: {name}")
            value = match.group(2)
            params[name] = (
                value.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
            )
            end = match.span()[1]
            params_xml_str = params_xml_str[end:]
        else:
            break
    return (tool_name, params)


def _get_agent_name(agent_file: str) -> str:
    agent_name, _ = os.path.splitext(os.path.basename(agent_file))
    return agent_name


def _get_prompt(task: str, tools: Optional[List[Callable]] = None):

    if tools:
        tools_prompt = """# Tool Use

You have access to a set of tools.
You can use one tool per message, and will receive the result of that tool use in the user's response.
You use tools step-by-step to accomplish a given task, with each tool use informed by the result of the previous tool use.

## Formatting

Tool use is formatted using XML-style tags.
The tool name is enclosed in opening and closing tags, and each parameter is similarly enclosed within its own set of tags.
Do not escape any characters, such as <, >, and & in XML tags. Do not wrap in `<![CDATA[` and `]]>`.
You can simply put multiline text in XML tags.
Always adhere to this format for the tool use to ensure proper parsing and execution. Here's the structure:

<tool_name>
<param1>...</param1>
<param2>...</param2>
...
</tool_name>

## Tools

"""

        for tool in tools:
            tools_prompt += f"### {tool.__name__}\n\n"
            if tool.__doc__:
                tools_prompt += f"Description: {tool.__doc__}"
            tools_prompt += "Usage:\n"
            tools_prompt += f"<{tool.__name__}>\n"
            for param in inspect.signature(tool).parameters.values():
                tools_prompt += f"<{param.name}>...</{param.name}>\n"
            tools_prompt += f"</{tool.__name__}>\n\n"

        logging.debug(tools_prompt)
    else:
        tools_prompt = ""

    return f"""You are my assistant to help me complete a task.
Once the task is complete, your reply must be enclosed in <result> and </result> to indicate the task is finished.
Here's my task:
-------
{task}
-------

{tools_prompt}
"""


class AgentMenu(ChatMenu):
    def __init__(
        self,
        context: Optional[Dict] = None,
        agent_file: Optional[str] = None,
        yes_always=True,
        run=False,
        load_last_agent=False,
        **kwargs,
    ):
        self.__run = run
        self.__yes_always = yes_always

        super().__init__(**kwargs)

        if agent_file:
            # Load specified agent
            self.__load_agent(agent_file, context=context)
        else:
            # Try to load last agent
            if load_last_agent and self.__load_last_agent():
                pass
            else:
                self.__new_agent()

        self.task_result: Optional[str] = None

        self.add_command(self.__add_tool, hotkey="alt+t")
        self.add_command(self.__edit_context, hotkey="alt+c")
        self.add_command(self.__edit_task, hotkey="alt+p")
        self.add_command(self.__list_agent, hotkey="ctrl+l")
        self.add_command(self.__load_last_agent, hotkey="alt+l")
        self.add_command(self.__new_agent, hotkey="ctrl+n")
        self.add_command(self.__check_code_blocks, hotkey="alt+enter")

    def __load_last_agent(self) -> bool:
        files = self.__get_agent_files()
        if len(files) > 0:
            self.__load_agent(files[-1])
            return True
        else:
            return False

    def __edit_context(self):
        self.__agent["context"].clear()
        self.__get_task_with_context()

    def __load_agent(
        self, agent_file: str, clear_messages=False, context: Optional[Dict] = None
    ):
        self.__agent_file = agent_file

        agent_default = {
            "task": "",
            "tools": get_all_tools(),
            "agents": [],
            "context": {},
        }
        if clear_messages:
            self.__agent = agent_default
        else:
            self.__agent = load_json(
                self.__agent_file,
                default=agent_default,
            )

        if context:
            self.__agent["context"].update(context)

        self.__update_prompt()

        conv_file = os.path.join(CHAT_DIR, _get_agent_name(self.__agent_file) + ".json")
        self.load_conversation(conv_file)
        if clear_messages:
            self.clear_messages()

        self.__tools = self.get_tools()

    def __update_prompt(self):
        tools = self.__agent["tools"]
        context = self.__agent["context"]
        self.set_prompt(
            f'agent="{_get_agent_name(self.__agent_file)}", '
            f"tools={tools}, "
            f"context={context}\n"
        )

    def __new_agent(self):
        agent_file = os.path.join(AGENT_DIR, UNSAVED_AGENT_FILE)
        self.__load_agent(agent_file, clear_messages=True)

    def __list_agent(self):
        menu = FileMenu(goto=AGENT_DIR)
        selected = menu.select_file()
        if selected:
            self.__load_agent(selected)

    def on_created(self):
        if self.__run:
            self.__complete_task()

    def on_message(self, content: str):
        self.__check_code_blocks()

    def send_message(self, text: str) -> None:
        if not text:
            self.__complete_task()
        else:
            i = len(self.get_messages())
            if i == 0:
                self.__agent["task"] = text
                self.__save_agent()
                self.__complete_task()
            else:
                super().send_message(text)

    def __get_agent_files(self) -> List[str]:
        return sorted(
            glob.glob(os.path.join(AGENT_DIR, "*.json")),
            key=os.path.getmtime,
        )

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
                        self.__agent["context"][name] = val
                        self.__save_agent()
            else:
                self.__update_prompt()
                return task

    def __complete_task(self):
        self.clear_messages()

        task = self.__get_task_with_context()

        super().send_message(
            _get_prompt(
                task=task,
                tools=self.__tools,
            )
        )

    def get_tools(self) -> List[Callable]:
        tools: List[Callable] = []
        for tool_name in self.__agent["tools"]:
            tools.append(load_tool(tool_name))

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

    def __check_code_blocks(self):
        messages = self.get_messages()
        if len(messages) <= 0:
            return

        selected_line = self.get_selected_item()
        if selected_line is None:
            return

        selected_message = self.get_messages()[selected_line.message_index]
        content = selected_message["content"]

        response_message = ""

        xml_strings = _find_xml_strings([t.__name__ for t in self.__tools], content)
        for xml_string in xml_strings:
            # Parse the XML string for the tool usage into valid Python code to be executed.
            tool_name, args = _parse_xml_string_for_tool(xml_string)

            # Run tool
            if not self.__yes_always:
                menu = ConfirmMenu("run tool?", items=[xml_string])
                menu.exec()
                should_run = menu.is_confirmed()
            else:
                should_run = True

            if should_run:
                tool = next(tool for tool in self.__tools if tool.__name__ == tool_name)
                ret = tool(**args)
                if ret:
                    response_message = "Returns:\n-------\n" + str(ret) + "\n-------"
                else:
                    response_message = "Done"

        # Check if the task is completed
        match = re.findall(
            r"<result>\s*([\S\s]*?)\s*</result>", content, flags=re.MULTILINE
        )
        if len(match) > 0:
            result = match[0]
            self.task_result = result if result else "Returns nothing."
            if self.__run:
                self.close()

            self.on_response(result, done=True)

        elif not response_message:
            self.on_response(content, done=False)

        if response_message:
            self.send_message(response_message)

    def on_response(self, text: str, done: bool):
        pass

    def __edit_task(self):
        self.__agent["task"] = self.call_func_without_curses(
            lambda: edit_text(self.__agent["task"])
        )
        self.__save_agent()
        self.__complete_task()

    def __add_tool(self):
        tools = get_all_tools()
        menu = Menu(items=tools)
        menu.exec()
        selected_tool = menu.get_selected_item()
        if selected_tool:
            self.__agent["tools"].append(selected_tool)
            self.__update_prompt()


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

    os.makedirs(SETTING_DIR, exist_ok=True)
    os.makedirs(AGENT_DIR, exist_ok=True)
    os.makedirs(CHAT_DIR, exist_ok=True)

    menu = AgentMenu(
        context=context,
        agent_file=args.agent,
        run=args.run,
        load_last_agent=True,
    )
    menu.exec()


if __name__ == "__main__":
    _main()
