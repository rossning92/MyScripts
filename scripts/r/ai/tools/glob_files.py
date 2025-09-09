import glob
import os


def glob_files(pattern) -> str:
    """
    Fast file pattern matching tool that works with any codebase size. Use this tool when you need to find files by name patterns.
    - Supports glob patterns like "**/*.js" or "src/**/*.ts"
    - Returns matching file paths sorted by modification time (newest first)
    - You should avoid using command line tools like `find` and `ls` in favor of `glob_files`
    """
    files = glob.glob(pattern, recursive=True)
    files.sort(key=os.path.getmtime, reverse=True)
    return "\n".join(files) + f"\n\nFound {len(files)} matching file(s)"
