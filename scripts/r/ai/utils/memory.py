from pathlib import Path
from typing import Optional

from ai.utils.rules import find_upward


def get_memory_file() -> Path:
    file = find_upward(Path.cwd(), "memory.md")
    if file:
        return file
    return Path.cwd() / "memory.md"


def get_memory_prompt() -> Optional[str]:
    memory_file = get_memory_file()

    # Load prompt template from file
    prompt_file = Path(__file__).resolve().parent.parent / "prompts" / "memory.txt"
    if not prompt_file.exists():
        return None
    template = prompt_file.read_text(encoding="utf-8").strip()

    content = ""
    if memory_file.exists():
        content = memory_file.read_text(encoding="utf-8").strip()

    if not content:
        # If there's no memory yet, return a simple instruction.
        init_prompt_file = Path(__file__).resolve().parent.parent / "prompts" / "memory_init.txt"
        if init_prompt_file.exists():
            template = init_prompt_file.read_text(encoding="utf-8").strip()
            return template.format(memory_file_name=memory_file.name)
        else:
            return f"""# Memory

You can maintain a `{memory_file.name}` file to store important information you want to remember across sessions. Use the `edit` tool to update it.
"""

    return template.format(memory_file_name=memory_file.name, content=content)
