def read_file(file: str):
    """Read a file at the specified path.
    Full file path must be provided if any."""

    with open(file, "r", encoding="utf-8") as f:
        return f.read()
