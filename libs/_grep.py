import glob
import os
import subprocess
import sys

import yaml
from _editor import open_in_editor
from _script import get_all_variables, get_data_dir
from _term import select_option


def search_code(text, root, extra_params=None):
    print("Search code in dir: %s" % root)
    args = [
        "rg",
        "-g",
        "!ThirdParty/",
        "-g",
        "!Extras/",
        "-g",
        "!Plugins/",
        "-F",
        text,
        "--line-number",
    ]
    if extra_params:
        args += extra_params
    # print(args)
    out = subprocess.check_output(
        args, shell=True, stderr=subprocess.PIPE, cwd=root, universal_newlines=True
    )
    print(out)

    result = []
    lines = out.split("\n")
    for line in lines:
        if line.strip() == "":
            continue
        arr = line.split(":")
        file_path = os.path.join(root, arr[0])
        line_no = arr[1]
        result.append((file_path, line_no))

    return result


def _open_bookmark(*, kw=None, path=None, repo=None, **kwargs):
    if kw is None and path is not None:
        open_in_editor(path)
    else:
        # Replace repo with repo absolute path
        variables = get_all_variables()
        variables = {k: v[0] for k, v in variables.items()}
        if repo in variables:
            repo = variables[repo]
            if not os.path.isdir(repo):
                raise Exception("Invalid repo path: %s" % repo)

        result = []
        if os.path.isdir(path):  # directory
            result += search_code(text=kw, root=path)
        else:  # file or glob
            result += search_code(text=kw, root=repo, extra_params=["-g", path])

        if len(result) == 1:
            open_in_editor(result[0][0], line_number=result[0][1])
        elif len(result) > 1:
            indices = select_option([f"{x[0]}:{x[1]}" for x in result])
            i = indices[0]
            open_in_editor(result[i][0], line_number=result[i][1])


def show_bookmarks(open_bookmark_func=None):
    def traverse_bookmark(bookmark, defaults={}):
        bookmark = {**defaults, **bookmark}
        # if "path" in bookmark:
        #     bookmark["path"] = bookmark["path"].format(**variables)
        return [bookmark]

    def traverse_item(item):
        bookmarks = []
        defaults = {}
        if "bookmarks" in item:
            for k, v in item.items():
                if k != "bookmarks":
                    defaults[k] = v
            for bookmark in item["bookmarks"]:
                assert "name" in bookmark
                bookmark["name"] = (
                    item["name"] + ": " if "name" in item else ""
                ) + bookmark["name"]
                bookmarks += traverse_bookmark(bookmark, defaults=defaults)
        else:
            bookmarks += traverse_bookmark(item, defaults=defaults)
        return bookmarks

    bookmarks = []
    for file in glob.glob(os.path.join(get_data_dir(), "bookmarks*.yml")):
        file = os.path.abspath(file)

        with open(file, "r") as f:
            lst = yaml.load(f.read(), Loader=yaml.FullLoader)

        for item in lst:
            bookmarks += traverse_item(item)

    names = [x["name"] for x in bookmarks]
    idx = select_option(names, history="show_bookmarks")
    if idx < 0:
        sys.exit(0)

    bookmark = bookmarks[idx]
    if open_bookmark_func is None:
        _open_bookmark(**bookmark)
    else:
        open_bookmark_func(**bookmark)
