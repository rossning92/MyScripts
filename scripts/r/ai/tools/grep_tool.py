import subprocess
from typing import List


def grep_tool(pattern: str) -> str:
    """
    Recursively searches the current directory for a regex pattern.
    - You MUST use `grep_tool` instead of command line search commands like `find` and `grep`.
    """

    max_lines = 1000

    # Run ripgrep command to search for the pattern
    process = subprocess.Popen(
        ["rg", "--heading", "--line-number", pattern],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Read output line by line
    terminated = False
    assert process.stdout is not None, "stdout should not be None"
    line_count = 0
    output_lines: List[str] = []
    for line in process.stdout:
        line = line.rstrip()
        output_lines.append(line)
        line_count += 1

        if line_count >= max_lines:
            process.terminate()  # Terminate the process early
            terminated = True
            break

    # Check for any errors
    if not terminated:
        return_code = process.wait()
        if return_code != 0:
            assert process.stderr is not None, "stderr should not be None"
            stderr = process.stderr.read()
            return f"Error occurred while searching: {stderr}"

    # Return the search results
    if not output_lines:
        return "No matches found."
    result = "\n".join(output_lines)
    if line_count >= max_lines:  # Add truncation message if max_lines are exceeded
        result += f"\n\n...\n\n[Output truncated, showing {max_lines} lines. Try narrowing your search pattern.]"
    return result
