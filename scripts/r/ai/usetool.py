import inspect
import logging
import re
from typing import Callable, List

from r.ai.openai.complete_chat import complete_chat


def use_tool(task: str, tools: List[Callable], max_replies=5) -> str:
    tool_list = ""
    for tool in tools:
        tool_list += f"- {tool.__name__}{inspect.signature(tool)}"
        if tool.__doc__:
            tool_list += f"  # {tool.__doc__}"
        tool_list += "\n"

    logging.debug(tool_list)

    initial_message = (
        f"""\
You are my assistant to help me complete a task.

You can call the following Python function at any time until my task can be completed:
{tool_list}

To call a function, respond with a valid Python function call wrapped in ```python and ```. I'll then reply with the function's return value. Here's an example:

```python
... call function here ...
```

If a task is completed, let me know the result.

Here's my task:
    """
        + task
    )

    message = {"role": "user", "content": initial_message}
    logging.debug(message)
    messages = [message]
    num_replies = 0
    while num_replies < max_replies:
        s = ""
        for chunk in complete_chat(messages):
            s += chunk
        s = s.strip()
        message = {"role": "assistant", "content": s}
        logging.debug(message)
        messages.append(message)

        match = re.findall(r"^\s*```python\n(.+?)\n\s*```", s, flags=re.MULTILINE)
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
