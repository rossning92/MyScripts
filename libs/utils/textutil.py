import os
import re
from typing import Optional

_RE_NEWLINES = re.compile(r"[\r\n]+")


def truncate_text(
    text: str,
    max_chars: int = 240,
    max_lines: Optional[int] = None,
) -> str:
    lines = text.splitlines()
    n_lines = len(lines)
    if max_lines is not None and n_lines > max_lines:
        text = "\n".join(lines[:max_lines])

    text = _RE_NEWLINES.sub(" ↵ ", text.strip())
    text = " ".join(text.split())

    if len(text) > max_chars or (max_lines and n_lines > max_lines):
        return f"{n_lines:2}|{text[:max_chars]}.."
    else:
        return text


def is_text_file(filepath: str, encoding="utf-8", buffer_size=4096, threshold=0.9):
    if not os.path.exists(filepath):
        return False

    if os.path.isdir(filepath):
        return False

    try:
        with open(filepath, "rb") as f:
            buffer = f.read(buffer_size)
        if not buffer:
            return True
        decoded = buffer.decode(encoding, errors="replace")
        total_chars = len(decoded)
        if total_chars == 0:
            return True
        invalid_chars = decoded.count("\ufffd")
        valid_ratio = (total_chars - invalid_chars) / total_chars
        return valid_ratio >= threshold

    except Exception as e:
        print(f"An error occurred while checking file {filepath}: {e}")
        return False
