import argparse
import inspect
import logging
import os
import re
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from ai.tools.execute_python import execute_python
from ai.tools.run_bash_command import run_bash_command
from ai.tools.write_file import write_file
from ML.gpt.chatmenu import ChatMenu
from utils.editor import edit_text
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


def _get_prompt(tools: Optional[List[Callable]] = None):
    if tools:
        tools_prompt = """# Tool Use

You can use the available tools to complete the user's task.

IMPORTANT:
- You MUST wait for the actual tool result before proceeding.

## Formatting

You MUST use the tools in the following format as part of your message. I will reply in the next message with the result of the tool use.
Tool use is formatted using XML-style tags.
The tool name is enclosed in opening and closing tags, and each parameter is similarly enclosed within its own set of tags.
Do not escape any characters in parameters, such as `<`, `>`, and `&`, in XML tags. Do not wrap parameters in `<![CDATA[` and `]]>`.
You can directly put multiline text in XML tags.
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
                tools_prompt += f"{tool.__doc__.strip()}\n"
            tools_prompt += "Usage:\n"
            tools_prompt += f"<{tool.__name__}>\n"
            for param in inspect.signature(tool).parameters.values():
                tools_prompt += f"<{param.name}>...</{param.name}>\n"
            tools_prompt += f"</{tool.__name__}>\n\n"

        logging.debug(tools_prompt)
    else:
        tools_prompt = ""

    return f"""You are my assistant to help me complete a task.
- Once the task is complete, your reply must be enclosed in <result> and </result> to indicate the task is finished.
- You should do what the user asks you to do, and nothing else.

# Tone

- You should be concise, direct, and to the point.
- You should answer the user's question directly without elaboration, explanation, or details, unless the user asks for them.
- You should keep your response to 1-2 sentences (not including tool use or code generation).
- You should NOT answer with unnecessary preamble or postamble (such as explaining your code or summarizing your action), unless the user asks you to.

# Code style

- Do not add comments to code unless the user requests it or the code is complex and needs context.
- You should follow existing code style, conventions, and utilize available libraries and utilities.

{tools_prompt}
""".rstrip()


class AgentMenu(ChatMenu):
    def __init__(
        self,
        context: Optional[Dict] = None,
        agent_file: Optional[str] = None,
        yes_always=True,
        run=False,
        load_last_agent=False,
        data_dir: str = DATA_DIR,
        **kwargs,
    ):
        self.__agent = AGENT_DEFAULT.copy()
        self.__agent_file = agent_file or os.path.join(data_dir, AGENT_FILE)
        self.__data_dir = data_dir
        self.__run = run
        self.__tools = self.get_tools()
        self.__yes_always = yes_always

        super().__init__(
            data_dir=data_dir,
            conv_file=os.path.join(self.__data_dir, "chat.json"),
            system_prompt=_get_prompt(tools=self.__tools),
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
        self.add_command(self.__edit_task)
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

        self.load_conversation()

    def __new_agent(self):
        self.__agent_file = os.path.join(self.__data_dir, AGENT_FILE)
        self.__agent = AGENT_DEFAULT.copy()
        self.new_conversation()

    def on_created(self):
        if self.__run:
            self.__complete_task()

    def on_message(self, content: str):
        self.__handle_response()

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

    def __complete_task(self):
        self.clear_messages()
        super().send_message(self.get_prompt())

    def get_tools(self) -> List[Callable]:
        tools: List[Callable] = [run_bash_command, execute_python, write_file]

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

    def __handle_response(self):
        messages = self.get_messages()
        if len(messages) <= 0:
            return

        selected_line = self.get_selected_item()
        if selected_line is None:
            return

        selected_message = self.get_messages()[selected_line.msg_index]
        content = selected_message["content"]

        reply = ""
        interrupted = False
        has_error = False
        xml_strings = _find_xml_strings([t.__name__ for t in self.__tools], content)
        for i, xml_string in enumerate(xml_strings):
            # Parse the XML string for the tool usage into valid Python code to be executed.
            tool_name, args = _parse_xml_string_for_tool(xml_string)

            # Run tool
            if not self.__yes_always:
                menu = ConfirmMenu(f"Run tool ({tool_name})?", items=[xml_string])
                menu.exec()
                if menu.is_confirmed():
                    should_run = True
                else:
                    should_run = False
                    reply += f"The {to_ordinal(i+1)} tool ({tool_name}) was interrupted by user.\n"
                    break
            else:
                should_run = True

            if should_run:
                tool = next(tool for tool in self.__tools if tool.__name__ == tool_name)
                try:
                    ret = tool(**args)
                    if ret:
                        reply += f"""The {to_ordinal(i+1)} tool ({tool_name}) returned:
-------
{str(ret)}
-------

"""

                    else:
                        reply += f"The {to_ordinal(i+1)} tool ({tool_name}) completed successfully.\n\n"
                except Exception as ex:
                    has_error = True
                    reply += f"""ERROR in the {to_ordinal(i+1)} tool ({tool_name}):
-------
{str(ex)}
-------

"""
                except KeyboardInterrupt:
                    reply += f"The {to_ordinal(i+1)} tool using {tool_name} was interrupted by user.\n"
                    interrupted = True
                    break

        # Check if the task is completed
        result = re.findall(
            r"<result>\s*([\S\s]*?)\s*</result>", content, flags=re.MULTILINE
        )
        if len(result) > 0:
            self.task_result = result[0] if result[0] else "Returns nothing."
            if self.__run:
                self.close()

            self.on_response(result[0], done=True)

        elif not reply:
            self.on_response(content, done=False)

        reply = reply.rstrip()
        if reply:
            if not has_error and (result or interrupted):
                self.append_user_message(reply)
            else:
                self.send_message(reply)

    def on_response(self, text: str, done: bool):
        pass

    def __edit_task(self):
        self.__agent["task"] = self.call_func_without_curses(
            lambda: edit_text(self.__agent["task"])
        )
        self.__save_agent()
        self.__complete_task()

    def __open_file_menu(self):
        FileMenu(goto=os.getcwd()).exec()

    def get_status_text(self) -> str:
        tools = "|".join([t.__name__ for t in self.get_tools()])
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
