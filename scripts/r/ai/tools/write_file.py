import os

from ai.tools.checkpoints import backup_files


def write_file(file: str, content: str):
    """Write content to a file at the specified path.
    If the file already exists, the original content will be overridden."""

    if os.path.exists(file):
        backup_files([file])

    with open(file, "w") as f:
        f.write(content)
