from typing import List, Tuple



def read_file_lines(file: str) -> Tuple[str, List[str]]:
    with open(file, "r", encoding="utf-8") as f:
        s = f.read()
        lines = s.splitlines()
    return s, lines


def read_file_from_line_range(file: str, start: int, end: int) -> str:
    _, lines = read_file_lines(file)
    start, end = max(1, start), min(end, len(lines))
    content = "\n".join(lines[start - 1 : end])
    return content


def replace_text_in_line_range(
    search: str, replace: str, content: str, start: int, end: int
) -> str:
    lines = content.split("\n")
    start, end = max(1, start), min(end, len(lines))
    target_region = "\n".join(lines[start - 1 : end])
    updated_region = target_region.replace(search.rstrip(), replace)
    updated_lines = lines[: start - 1] + updated_region.split("\n") + lines[end:]
    updated_content = "\n".join(updated_lines)
    return updated_content


def apply_change(file: str, search: str, replace: str):
    # If search block is empty, create a new file
    if not search:
        with open(file, "w", encoding="utf-8") as f:  # Create a new file
            f.write(replace)
    else:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
            if "\r\n" in content:
                newline = "\r\n"
            else:
                newline = "\n"

        count = content.count(search)
        if count == 0:
            raise ValueError(f'Cannot find any match in "{file}":\n```\n{search}\n```')
        elif count > 1:
            raise ValueError(
                f'Found more than one match in "{file}". '
                "Try adding some surrounding lines in order to uniquely match the search block:\n"
                f"```\n{search}\n```"
            )
        content = content.replace(search, replace)

        # Save file
        with open(file, "w", encoding="utf-8", newline=newline) as f:
            f.write(content)

