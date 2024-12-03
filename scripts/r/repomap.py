import glob
import json
import logging
import os
import subprocess
import sys
from typing import List


def get_ctags(filename: str) -> List:
    cmd = [
        "ctags",
        "--fields=+S",
        "--extras=-F",
        "--output-format=json",
        "--output-encoding=utf-8",
        "--input-encoding=utf-8",
        filename,
    ]
    output = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode("utf-8")
    tags = []
    for line in output.splitlines():
        tags.append(json.loads(line))
    return tags


def to_tree(tags, scope="", indent=""):
    if not tags:
        return ""

    output = ""
    for tag in filter(
        lambda tag: (not scope and "scope" not in tag)
        or ("scope" in tag and tag["scope"] == scope),
        tags,
    ):
        name = tag["name"]
        prefix = "class " if tag["kind"] == "class" else ""
        signature = tag["signature"] if "signature" in tag else ""
        output += f"{indent}{prefix}{name}{signature}\n"
        output += to_tree(
            tags,
            scope=scope + "." + name if scope else name,
            indent=indent + (" " * 2),
        )

    return output


def get_repomap(pathname: str) -> str:
    output = ""

    for fname in list(glob.glob(pathname)):
        print(fname)
        if os.path.isdir(fname):
            logging.warning(f"Skip directory {fname}")
            continue

        output += fname + "\n"

        tags = get_ctags(fname)
        output += to_tree(tags, indent=" " * 2) + "\n"

    return output


if __name__ == "__main__":
    print(get_repomap(sys.argv[-1]))
