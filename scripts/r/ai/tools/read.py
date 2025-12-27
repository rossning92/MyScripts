from itertools import islice


def read(file: str, offset: int = 0, limit: int = 2000) -> str:
    """Read up to `limit` lines from `file`, starting at `offset` (0-based)."""

    if limit <= 0:
        return f"ERROR: limit must be > 0 (got {limit})"

    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        for _ in range(offset):
            if not f.readline():
                return f"ERROR: offset {offset} is beyond end of file"

        lines = list(islice(f, limit))
        next_line = f.readline()

        if not next_line:
            return "".join(lines)

        remaining = 1 + sum(1 for _ in f)
        total = offset + len(lines) + remaining
        result = "".join(lines)
        return (
            result + f"\n[File has more lines: remaining {remaining} / total {total}]"
        )
