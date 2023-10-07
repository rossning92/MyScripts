from typing import Callable, List, Optional, Tuple

from _script import (
    get_all_scripts,
    get_relative_script_path,
)
from utils.menu import Menu


def find_in_all_scripts(
    s: str,
    on_progress: Optional[Callable[[str], None]] = None,
) -> List[Tuple[str, int, str]]:
    modified_lines: List[Tuple[str, int, str]] = []

    files = list(get_all_scripts())

    for i, file in enumerate(files):
        if on_progress is not None:
            if i % 20 == 0:
                on_progress("searching (%d/%d)" % (i + 1, len(files)))

        try:
            with open(file, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()

            for i, line in enumerate(lines):
                if s in line:
                    modified_lines.append(
                        (get_relative_script_path(file), i + 1, lines[i])
                    )

        except UnicodeDecodeError:
            pass

    return modified_lines


if __name__ == "__main__":
    lines = find_in_all_scripts("hello")
    w = Menu(
        label="find in all scripts", items=[f"{x[0]}:{x[1]}:\t{x[2]}" for x in lines]
    )
    w.exec()
