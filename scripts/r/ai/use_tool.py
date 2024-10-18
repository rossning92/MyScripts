import inspect
import logging
import re
from typing import Callable, List

from r.ai.openai.complete_chat import complete_messages
from utils.logger import setup_logger


def use_tool(text: str, tools: List[Callable], max_replies=5) -> str:
    tool_list = ""
    for tool in tools:
        tool_list += f"- {tool.__name__}{inspect.signature(tool)}"
        if tool.__doc__:
            tool_list += f"  # {tool.__doc__}"
        tool_list += "\n"

    logging.debug(tool_list)

    initial_message = (
        f"""
You are my assistant and help me complete an action.

To complete my request, you can call the following Python function any time until the request can be fullfilled:
{tool_list}

If you want to call a function, you must only return a valid Python function call wrapped with ` and nothing else. I'll reply you with the function return value.

if a request can be fullfilled, just tell me the result and I'll end the conversation.

Here is my request:
    """
        + text
    )

    message = {"role": "user", "content": initial_message}
    logging.debug(message)
    messages = [message]
    num_replies = 0
    while num_replies < max_replies:
        s = ""
        for chunk in complete_messages(messages):
            s += chunk
        s = s.strip()
        message = {"role": "assistant", "content": s}
        logging.debug(message)
        messages.append(message)

        match = re.findall("`.*?`", s)
        if len(match) == 1:
            s = match[0].strip("`")
            result = eval(
                s,
                {tool.__name__: tool for tool in tools},
            )
            message = {"role": "user", "content": f"The function returns: {result}"}
            logging.debug(message)
            messages.append(message)
        else:
            break

        num_replies += 1
    if num_replies >= max_replies:
        raise Exception(f"Max replies have reached: {max_replies}")

    return s


def _main():
    def add(a: int, b: int) -> int:
        return a + b

    def multiply(a: int, b: int) -> int:
        return a * b

    def power(a: int, b: int) -> int:
        n = 1
        for _ in range(b):
            n *= a
        return n

    result = use_tool("What is 2 to the power of 8?", tools=[add, multiply, power])
    logging.debug(f"Result: {result}")


if __name__ == "__main__":
    setup_logger()
    _main()
