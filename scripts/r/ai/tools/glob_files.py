import glob
import os


def glob_files(pattern) -> str:
    """Finds files by name and pattern.
    Returns matching paths sorted by modification time in descending order.

    Examples:
    - '*.js' - Find all JavaScript files in the current directory
    - '**/*.md' - Find all Markdown files in any subdirectory
    - 'src/**/*.{ts,tsx}' - Find all TypeScript files in the src directory
    """
    files = glob.glob(pattern, recursive=True)
    files.sort(key=os.path.getmtime, reverse=True)
    return "\n".join(files) + f"\n\nFound ${len(files)} matching file(s)`"
