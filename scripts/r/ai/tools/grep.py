import argparse
import subprocess
from typing import List

MAX_LINES = 1000


def grep(regex: str) -> str:
    """
    Fast content search tool for any codebase size that finds files with specific patterns in their content.

    - Recursively searches file contents from the current directory.
    - Supports full regular expression pattern matching.
    - IMPORTANT: Always use `grep_tool` instead of command-line tools like `find` or `grep` for searches.
    """

    # Run ripgrep command
    process = subprocess.Popen(
        ["rg", "--heading", "--line-number", regex],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Redirect stderr to stdout
        text=True,
    )

    # Read output line by line
    assert process.stdout is not None, "stdout should not be None"
    line_count = 0
    lines: List[str] = []

    # Process combined stdout and stderr
    for line in process.stdout:
        line = line.rstrip()
        lines.append(line)
        line_count += 1

        if line_count >= MAX_LINES:
            process.terminate()  # Terminate the process early
            break

    process.wait()

    # Return the search results
    if not lines:
        return "No matches found"
    result = "\n".join(lines)
    if line_count >= MAX_LINES:  # Add truncation message if max_lines are exceeded
        result += f"\n\n[Output truncated, showing only {MAX_LINES} lines. Please try narrowing your search]"
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("regex")
    args = parser.parse_args()

    result = grep(args.regex)
    print(result)
