import argparse
import os
from io import StringIO
from itertools import islice
from pathlib import Path
from typing import Union


def tree(
    dir_path: Union[Path, str],
    max_level: int = -1,
    limit_to_directories: bool = False,
    length_limit: int = 1000,
):
    space = "    "
    branch = "│   "
    tee = "├── "
    last = "└── "

    output = StringIO()
    dir_path = Path(dir_path)  # accept string coerceable to Path
    files = 0
    directories = 0

    def inner(dir_path: Path, prefix: str = "", level=-1):
        nonlocal files, directories
        if not level:
            return  # 0, stop iterating
        if limit_to_directories:
            contents = [d for d in dir_path.iterdir() if d.is_dir()]
        else:
            contents = list(dir_path.iterdir())
        pointers = [tee] * (len(contents) - 1) + [last]
        for pointer, path in zip(pointers, contents):
            if path.is_dir():
                yield prefix + pointer + path.name + "/"
                directories += 1
                extension = branch if pointer == tee else space
                yield from inner(path, prefix=prefix + extension, level=level - 1)
            elif not limit_to_directories:
                yield prefix + pointer + path.name
                files += 1

    output.write(dir_path.name + "\n")
    iterator = inner(dir_path, level=max_level)
    for line in islice(iterator, length_limit):
        output.write(line + "\n")
    if next(iterator, None):
        output.write(f"... length_limit, {length_limit}, reached, counted:\n")
    output.write(f"\n{directories} directories" + (f", {files} files" if files else ""))
    return output.getvalue()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=os.getcwd())
    args = parser.parse_args()

    print(tree(dir_path=args.path))
