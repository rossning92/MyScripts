import os
import re
import subprocess
import tempfile
import time
import uuid

from ai.utils.tools import Settings
from utils.menu.confirmmenu import confirm
from utils.menu.menu import Menu
from utils.term import clear_terminal

TRUSTED_COMMANDS = ["ls", "pwd", "date"]


def _run_script(command: str, log_file: str) -> None:
    clear_terminal()
    subprocess.run(["script", "-q", "-e", "-c", command, log_file], check=False)


def _run_bash(command: str) -> str:
    # Use a temporary file to capture command output
    with tempfile.NamedTemporaryFile(delete=False) as f:
        log_file = f.name

    try:
        # Run command interactively using 'script' (-q: quiet, -e: return exit code, -c: run command)
        Menu.run_raw(lambda: _run_script(command, log_file))

        # Read the captured output
        with open(log_file, "r") as f:
            output = f.read()

        output = re.sub(r"^Script started on .*\n?", "", output)
        output = re.sub(r"Script done on .*", "", output.strip())
        return output.replace("\r", "").strip()
    finally:
        # Clean up the temporary file
        if os.path.exists(log_file):
            os.remove(log_file)


def _save_full_output(output: str, tool_name: str) -> str:
    output_dir = os.path.join(tempfile.gettempdir(), "coder", "tool-output")
    os.makedirs(output_dir, exist_ok=True)

    full_output_filename = (
        f"tool_{tool_name}_{int(time.time())}_{uuid.uuid4().hex[:8]}.log"
    )
    full_output_path = os.path.join(output_dir, full_output_filename)
    with open(full_output_path, "w", encoding="utf-8") as f:
        f.write(output)
    return full_output_path


def _truncate_output(output: str, tool_name: str) -> str:
    MAX_OUTPUT_LINES = 2000
    MAX_OUTPUT_BYTES = 50 * 1024

    lines = output.splitlines()
    if (
        len(lines) <= MAX_OUTPUT_LINES
        and len(output.encode("utf-8")) <= MAX_OUTPUT_BYTES
    ):
        return output

    full_output_path = _save_full_output(output, tool_name)

    # Truncate to MAX_OUTPUT_LINES
    truncated_lines = lines[:MAX_OUTPUT_LINES]
    preview = "\n".join(truncated_lines)

    # Further truncate if still exceeds MAX_OUTPUT_SIZE
    preview_bytes = preview.encode("utf-8")
    if len(preview_bytes) > MAX_OUTPUT_BYTES:
        preview = (
            preview_bytes[:MAX_OUTPUT_BYTES].decode("utf-8", errors="ignore")
            + "\n... [preview truncated]"
        )

    num_truncated = len(lines) - len(preview.splitlines())

    return (
        f"{preview}\n"
        f"... {num_truncated} lines truncated ...\n"
        f"Output was truncated, full output saved to: {full_output_path}\n"
        "Use `grep` to search the entire content, or use `read` with offset and limit to view specific sections"
    )


def bash(command: str) -> str:
    """
    Execute a bash command on the system.
    - Use this when you need to perform system operations or run specific commands to accomplish any step in the user's task.
    - Ensure the command is properly formatted and does not contain any harmful instructions.
    """

    need_confirm = True
    for cmd in TRUSTED_COMMANDS:
        pattern = re.escape(cmd).replace(r"\*", ".*")
        if re.match(rf"^\s*{pattern}(?:\s+|$)", command):
            need_confirm = False
            break

    if Settings.need_confirm and need_confirm and not confirm(f"Run `{command}`?"):
        raise KeyboardInterrupt("Command execution was canceled by the user")

    output = _run_bash(command)

    return _truncate_output(output, tool_name="bash")
