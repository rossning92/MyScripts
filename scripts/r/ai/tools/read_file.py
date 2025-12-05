from typing import List


def read_file(file: str, offset: int = 0, limit: int = 2000):
    """
    Read a file at the specified path.

    Parameters:
        file: Path to the file to read
        offset: Number of lines to skip from the beginning (0-based)
        limit: Maximum number of lines to read after the offset
    """

    lines: List[str] = []
    truncated = False

    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        for _ in range(offset):
            if not f.readline():
                return ""

        for _ in range(limit):
            line = f.readline()
            if not line:
                return "".join(lines)
            lines.append(line)

        if f.readline():
            truncated = True

    result = "".join(lines)
    if truncated:
        result += "\n[File has more lines]"
    return result
