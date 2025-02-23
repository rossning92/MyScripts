import importlib
import os
from typing import Callable

TOOLS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools")


def get_all_tool_names():
    modules = [
        os.path.basename(os.path.splitext(f)[0])
        for f in os.listdir(TOOLS_PATH)
        if f.endswith(".py")
    ]
    return modules


def load_tool(name: str) -> Callable:
    module_name = f"tools.{name}"
    read_webpage_module = importlib.import_module(module_name)

    function = getattr(read_webpage_module, name)
    if not callable(function):
        raise Exception(f"Cannot find {name} in module {name}")

    return function
