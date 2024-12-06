import importlib
import os
from typing import Callable

TOOLS_PATH = "tools"


def get_all_tools():
    modules = [
        os.path.splitext(f)[0] for f in os.listdir(TOOLS_PATH) if f.endswith(".py")
    ]
    return modules


def load_tool(name: str) -> Callable:
    module_name = f"{TOOLS_PATH}.{name}"
    read_webpage_module = importlib.import_module(module_name)

    function = getattr(read_webpage_module, name)
    if not callable(function):
        raise Exception(f"Cannot find {name} in module {name}")

    return function
