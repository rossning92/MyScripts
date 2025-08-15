from pprint import pprint

from ai.anthropic.chat import complete_chat
from utils.logger import setup_logger
from utils.printc import printc

setup_logger()

messages = [{"role": "user", "content": "What's the weather like in San Francisco?"}]
out = complete_chat(
    messages=messages,
    tools=[
        {
            "name": "get_weather",
            "description": "Get the current weather in a given location",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    }
                },
                "required": ["location"],
            },
        }
    ],
)
for s in out:
    printc(s, end="")

pprint(messages[-1]["content"])
