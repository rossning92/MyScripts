from pathlib import Path
from typing import Optional

from ai.utils.env import get_global_config_path


def find_upward(path: Path, name: str) -> Optional[Path]:
    curr = path.resolve()
    while True:
        target = curr / name
        if target.exists():
            return target
        if curr == curr.parent:
            break
        curr = curr.parent
    return None


def get_project_rule_file(data_dir: str, rule_file: str) -> Path:
    file = find_upward(Path.cwd(), rule_file)
    if file:
        return file
    return Path(data_dir) / rule_file


def get_rule_files(data_dir: str, rule_file: str) -> list[Path]:
    files = [get_project_rule_file(data_dir, rule_file)]

    if config_path := get_global_config_path():
        for name in [rule_file, "agent.md", "AGENTS.md"]:
            path = config_path / name
            if path.exists() and path not in files:
                files.append(path)
                break

    return files


def get_rules_prompt(data_dir: str, rule_file: str = "AGENTS.md") -> str:
    files = get_rule_files(data_dir, rule_file)

    contents = []
    for file in files:
        if file.exists():
            s = file.read_text(encoding="utf-8").strip()
            if s:
                contents.append(f'<file path="{file}">\n{s}\n</file>')

    return "\n\n".join(contents)
