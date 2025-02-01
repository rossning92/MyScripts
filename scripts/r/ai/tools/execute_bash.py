import subprocess


def execute_bash(command: str) -> str:
    """Execute a bash command on the system.
    Use this when you need to perform system operations or run specific commands to accomplish any step in the user's task.
    Ensure the command is properly formatted and does not contain any harmful instructions.
    """

    try:
        completed_process = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        output = completed_process.stdout
    except subprocess.CalledProcessError as e:
        output = f"Command failed with return code {e.returncode}\n{e.stdout}"
    return output
