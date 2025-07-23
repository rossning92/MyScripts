from ai.codeeditutils import Change, apply_change, apply_change_interactive
from ai.tools import Settings
from ai.tools.checkpoints import backup_files


def edit_file(file: str, old_string: str, new_string: str):
    """Edit a portion of a file as specified by `old_string` and replace it with the `new_string`.

    The `old_string` MUST uniquely identify the instance you want to change. If multiple matches exist, add some surrounding lines to uniquely identify the instance.
    The `old_string` string MUST exactly match existing content, including whitespace and indentation, as it appears in the file.
    You can use this tool multiple times to make multiple changes across multiple files in a single request.
    This tool is intended to make small edits. To create a new file, or replace the entire file content, use `write_file` instead.
    """
    backup_files([file])

    change = Change(file=file, search=old_string, replace=new_string)
    if Settings.need_confirm:
        if not apply_change_interactive(change=change):
            raise KeyboardInterrupt("Search and replace was canceled by the user")
    else:
        apply_change(change=change)
