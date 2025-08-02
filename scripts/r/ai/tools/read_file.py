def read_file(file: str):
    """
    Read a file at the specified path.
    """

    with open(file, "r", encoding="utf-8") as f:
        return f.read()
