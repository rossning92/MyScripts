def write_file(file: str, text: str):
    """Write text to a file.
    If the file already exists, the original content will be overridden."""

    with open(file, "w") as f:
        f.write(text)
