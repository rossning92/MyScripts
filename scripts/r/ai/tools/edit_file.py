from ai.codeeditutils import Change, apply_change, apply_change_interactive
from ai.tools import Settings
from utils.checkpoints import backup_files


def edit_file(file: str, old_string: str, new_string: str):
    """
    Edit a portion of a file as specified by `old_string` and replace it with the `new_string`.
    - The `old_string` MUST uniquely identify the instance you want to change. If multiple matches exist, add some surrounding lines to uniquely identify the instance.
    - The `old_string` string MUST exactly match existing content, including whitespace and indentation, as it appears in the file.
    - You can use `edit_file` multiple times to make multiple changes across multiple files in a single request.
    - You should use the `edit_file` tool for small edits. To create a new file or replace the entire file content, use `write_file` instead.
    """
    backup_files([file])

    change = Change(file=file, search=old_string, replace=new_string)
    if Settings.need_confirm_edit_file:
        if not apply_change_interactive(change=change):
            raise KeyboardInterrupt("Search and replace was canceled by the user")
    else:
        apply_change(change=change)
