from _term import *
from _shutil import *
from _editor import *


def grep(src_dir, exclude=[]):
    repo_root = None
    rel_path = None

    if False:
        tmp_path = ""
        for comp in src_dir.split("\\"):
            tmp_path += comp + "\\"
            if exists(tmp_path + ".gitignore"):
                print("REPO ROOT: " + tmp_path)
                repo_root = tmp_path
                rel_path = src_dir.replace(repo_root, "")
                print(rel_path)
                break

        input()

    if repo_root:
        chdir(repo_root)
    else:
        chdir(src_dir)
    print2("Source Dir: %s" % src_dir)

    text = input("KEYWORD> ")
    if text == "":
        sys.exit(0)

    args = 'rg -g "*.{c,h,cpp}" --line-number -F "%s"' % text
    if rel_path:
        args += " " + rel_path

    if not exists(".gitignore"):
        args += ' -g "!intermediates/" -g "!build/" -g "!Build/"'
    for x in exclude:
        args += ' -g "!%s"' % x

    args += " | peco"
    print2(args, color="cyan")

    out = get_output(args)

    file, line_number, *_ = out.split(":")
    line_number = int(line_number)
    print("Goto: %s: %d" % (file, line_number))
    open_in_vscode(file, line_number)


if __name__ == "__main__":
    grep(src_dir=r"{{SOURCE_FOLDER}}", exclude="{{_EXCLUDE}}".split())
