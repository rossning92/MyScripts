import glob
import os


def glob_files(pattern) -> str:
    """
    Finds files by name and pattern and returns matching paths sorted by modification time in descending order.
    - You MUST always use `glob_files` and avoid command line tools like `find` and `ls`.

    Examples:
    - '*.js' - Find all JavaScript files in the current directory
    - '**/*.md' - Find all Markdown files in any subdirectory
    """
    files = glob.glob(pattern, recursive=True)
    files.sort(key=os.path.getmtime, reverse=True)
    return "\n".join(files) + f"\n\nFound {len(files)} matching file(s)"
