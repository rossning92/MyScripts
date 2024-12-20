import argparse
import glob
import inspect
import io
import logging
import os
import re
import traceback
from contextlib import redirect_stdout
from pathlib import Path
from typing import Callable, Dict, List, Optional

from ai.toolutil import get_all_tools, load_tool
from ML.gpt.chatmenu import ChatMenu
from utils.editor import edit_text
from utils.exec_then_eval import exec_then_eval
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


def _get_agent_name(agent_file: str) -> str:
    agent_name, _ = os.path.splitext(os.path.basename(agent_file))
    return agent_name


def _get_prompt(
    task: str,
    tools: Optional[List[Callable]] = None,
    code_execution=True,
):

    code_execution_prompt = (
        """\
You can execute Python code anytime to complete the task.
If a task can be completed without Python code, just provide the result directly.
To do so, provide valid Python code block using the following format:
```python
... python code ...
```
Avoid using third-party libraries.
Don't add any comments into the code.
Return Python code block only, nothing else.
I'll run the code and reply to you with the output.
"""
        if code_execution
        else ""
    )

    if tools:
        tools_prompt = "You can call the following Python functions anytime to complete the task:\n"

        for tool in tools:
            tools_prompt += f"* {tool.__name__}{inspect.signature(tool)}"
            if tool.__doc__:
                tools_prompt += f"  # {tool.__doc__}"
            tools_prompt += "\n"

        tools_prompt += """
You must provide a valid Python function call using the following format:
```python
... function call ...
```
I'll run the code and reply to you with the return value.
Don't explain, don't add any comments.
Only one Python function call is allowed per message.
"""
        logging.debug(tools_prompt)
    else:
        tools_prompt = ""

    return f"""\
You are my assistant to help me complete a task.

{code_execution_prompt}

{tools_prompt}

Once the task is complete, you must reply with the result enclosed in <result> and </result>.

Here's my task:
-------
{task}
-------
"""


class PyAgentMenu(ChatMenu):
    def __init__(
        self,
        context: Optional[Dict] = None,
        agent_file: Optional[str] = None,
        yes_always=True,
        run=False,
        **kwargs,
    ):
        self.__run = run
        self.__yes_always = yes_always
        self.__globals: Dict = {}

        super().__init__(**kwargs)

        # Load agent
        if agent_file:
            self.__load_agent(agent_file, context=context)
        else:
            agent_files = self.__get_agent_files()
            if len(agent_files) > 0:
                self.__load_agent(agent_files[-1])
            else:
                self.__new_agent()

        self.task_result: Optional[str] = None

        self.add_command(self.__edit_task, hotkey="alt+p")
        self.add_command(self.__list_agent, hotkey="ctrl+l")
        self.add_command(self.__new_agent, hotkey="ctrl+n")
        self.add_command(self.__add_tool, hotkey="alt+t")
        self.add_command(self.__edit_context, hotkey="alt+c")

    def __edit_context(self):
        self.__agent["context"].clear()
        self.__get_task_with_context()

    def __load_agent(
        self, agent_file: str, clear_messages=False, context: Optional[Dict] = None
    ):
        self.__agent_file = agent_file
        self.__agent = load_json(
            self.__agent_file,
            default={"task": "", "tools": [], "agents": [], "context": {}},
        )

        if context:
            self.__agent["context"].update(context)

        self.__update_prompt()

        conv_file = os.path.join(CHAT_DIR, _get_agent_name(self.__agent_file) + ".json")
        self.load_conversation(conv_file)
        if clear_messages:
            self.clear_messages()

    def __update_prompt(self):
        task = self.__agent["task"].strip()

        prompt = f"""\
  agent : {_get_agent_name(self.__agent_file)}
&prompt : {task.splitlines()[0] if task else ''}
 &tools : {self.__agent['tools']}
   &ctx : {self.__agent['context']}
-------
"""
        self.set_prompt(prompt)

    def __new_agent(self):
        i = 1
        while True:
            agent_file = os.path.join(AGENT_DIR, f"agent{i}.json")
            if os.path.exists(agent_file):
                i += 1
            else:
                break

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

    def on_enter_pressed(self):
        text = self.get_input().strip()
        if not text:
            self.__complete_task()
        else:
            i = len(self.get_messages())
            if i == 0:
                self.__agent["task"] = self.get_input()
                self.__save_agent()
                self.__complete_task()
            else:
                return super().on_enter_pressed()

    def __get_agent_files(self) -> List[str]:
        return sorted(
            glob.glob(os.path.join(AGENT_DIR, "*.json")),
            key=os.path.getmtime,
        )

    def __save_agent(self):
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

        self.__tools = self.__get_tools()
        self.__globals.update({t.__name__: t for t in self.__tools})

        task = self.__get_task_with_context()

        self.send_message(
            _get_prompt(
                task=task,
                tools=self.__tools,
            )
        )

    def __get_tools(self):
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
                menu = PyAgentMenu(
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

        # Check if any Python code blocks are returned.
        response_message = ""
        blocks = re.findall(
            r"```python\n([\S\s]+?)\n\s*```", content, flags=re.MULTILINE
        )
        if len(blocks) > 0:
            should_run = True
            if not self.__yes_always:
                menu = ConfirmMenu("run command?", items=blocks)
                menu.exec()
                should_run = menu.is_confirmed()

            if should_run:
                for block in blocks:
                    with io.StringIO() as buf, redirect_stdout(buf):
                        success = False
                        try:
                            return_val = exec_then_eval(
                                block,
                                globals=self.__globals,
                            )
                            success = True
                        except Exception:
                            tb = traceback.format_exc()
                            Menu(items=tb.splitlines()).exec()

                        if success:
                            stdout = buf.getvalue()
                            if return_val is not None or stdout:
                                output = ""
                                if stdout:
                                    output += stdout
                                if return_val is not None:
                                    if output:
                                        output += "\n"
                                    output += str(return_val)
                                response_message = output
                            else:
                                response_message = (
                                    "The Python code finishes successfully."
                                )

        # Check if the task is completed
        match = re.findall(
            r"<result>\s*([\S\s]*?)\s*</result>", content, flags=re.MULTILINE
        )
        if len(match) > 0:
            result = match[0]
            self.set_message(f"result: {result}")
            self.task_result = result if result else "Returns nothing."
            if self.__run:
                self.close()

        if response_message:
            self.send_message(response_message)

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

    menu = PyAgentMenu(
        yes_always=True, context=context, agent_file=args.agent, run=args.run
    )
    menu.exec()


if __name__ == "__main__":
    _main()
