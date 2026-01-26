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


def get_rule_file(data_dir: str, rule_file: str) -> Path:
    file = find_upward(Path.cwd(), rule_file)
    if file:
        return file
    return Path(data_dir) / rule_file


def get_rules_prompt(data_dir: str, rule_file: str = "AGENTS.md") -> str:
    file = get_rule_file(data_dir, rule_file)
    if not file.exists():
        return ""

    s = file.read_text(encoding="utf-8").strip()
    if not s:
        return ""

    return f"# General Instructions\n\n{s}\n"
