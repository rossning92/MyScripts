from ai.codeeditutils import Change, apply_change_interactive


def search_and_replace(file: str, search: str, replace: str):
    """Modify a specific section of a file and replace it with the provided content.
    Include just the changing lines, and a few surrounding lines if needed for uniqueness.
    The search string must exactly match existing content including whitespace and indentation.
    You can use this tool multiple times to make multiple changes across multiple files in a single request.
    For small chunks of file edits, it is preferred to use `search_and_replace` rather than `write_file` to overwrite the full file content.
    """

    if not apply_change_interactive(
        changes=[Change(file=file, search=search, replace=replace)]
    ):
        raise KeyboardInterrupt("Search and replace was canceled by the user")
