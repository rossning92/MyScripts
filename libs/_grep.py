from _appmanager import get_executable
from _editor import open_in_vscode
from _shutil import *
from _term import search


def search_code(text, search_path, extra_params=None):
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
        args, shell=True, stderr=subprocess.PIPE, cwd=search_path
    )
    out = out.decode()
    print(out)

    result = []
    lines = out.split("\n")
    for line in lines:
        if line.strip() == "":
            continue
        arr = line.split(":")
        file_path = os.path.join(search_path, arr[0])
        line_no = arr[1]
        result.append((file_path, line_no))

    return result


def search_code_and_goto(text, path_list):
    assert type(path_list) == list  # `path` must be a list
    print2(str(path_list))
    result = []
    for path in path_list:
        if os.path.isdir(path):  # directory
            result += search_code(text=text, search_path=path)
        else:  # file or glob
            if "/**/" in path:
                dir_path, file_name = path.split("/**/")
                result += search_code(
                    text=text, search_path=dir_path, extra_params=["-g", file_name]
                )

    if len(result) == 1:
        open_in_vscode(result[0][0], line_number=result[0][1])
    elif len(result) > 1:
        indices = search([f"{x[0]}:{x[1]}" for x in result])
        i = indices[0]
        open_in_vscode(result[i][0], line_number=result[i][1])


def show_bookmarks(bookmarks):
    names = [x["name"] for x in bookmarks]
    idx = search(names)
    if idx == -1:
        sys.exit(0)

    bookmark = bookmarks[idx]

    if "kw" in bookmark:
        search_code_and_goto(bookmark["kw"], path_list=bookmark["path"])
    else:
        open_in_vscode(bookmark["path"])


if __name__ == "__main__":
    open_in_vscode(sys.argv[1])
