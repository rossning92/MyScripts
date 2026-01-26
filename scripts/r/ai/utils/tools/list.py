import glob
import os


def list(path: str) -> str:
    """
    Lists files and directories in a given path.
    - You MUST always use the `list_files` tool instead of commands like `ls`.
    """
    if not os.path.exists(path):
        raise Exception(f'Path "{path}" does not exist')

    files = glob.glob(os.path.join(path, "*"))
    result = []

    for file in sorted(files):
        filename = os.path.basename(file)
        if os.path.isdir(file):
            result.append(f"{filename}/")
        else:
            result.append(filename)

    return "\n".join(result) if result else "No files found"
