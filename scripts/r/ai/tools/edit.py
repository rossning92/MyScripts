import os

from ai.codeeditutils import apply_change
from utils.checkpoints import backup_files


def edit(file: str, old_string: str, new_string: str):
    """
    Replace ONE occurrence of old_string with new_string in the specified file.
    - The old_string MUST uniquely identify the instance you want to change. If multiple matches exist, add some surrounding lines to uniquely identify the instance.
    - The old_string string MUST exactly match existing content, including whitespace and indentation, as it appears in the file.
    - This tool can only change one instance at a time. If you need to change multiple instances, make separate calls to this tool for each instance.
    - If you want to create a new file, use: a new file path; an empty old_string; the new file's contents as new_string.
    """
    if os.path.exists(file):
        backup_files([file])

    apply_change(file=file, search=old_string, replace=new_string)
