import os
from pathlib import Path
from typing import Optional


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

    custom_rules = os.environ.get("AI_CUSTOM_RULES")
    if custom_rules:
        for path_str in custom_rules.split(os.pathsep):
            path_str = path_str.strip()
            if path_str:
                path = Path(path_str).expanduser().resolve()
                if path.exists() and path not in files:
                    files.append(path)

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
