import os

from _editor import open_in_vscode
from _shutil import chdir, get_output, load_json, print2, save_json
from _term import Menu


def grep(src_dir, exclude=[]):
    if not os.path.exists(src_dir):
        raise Exception("Path does not exist: %s" % src_dir)

    repo_root = None
    rel_path = None

    if False:
        tmp_path = ""
        for comp in src_dir.split("\\"):
            tmp_path += comp + "\\"
            if os.path.exists(tmp_path + ".gitignore"):
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

    while True:
        history = load_json("grep_code.json", default=[])
        w = Menu(items=history)
        w.exec()
        input_str = w.get_text()
        if not input_str:
            continue

        history = [x for x in history if x != input_str]
        history.insert(0, input_str)
        save_json("grep_code.json", history)

        args = 'rg -g "*.{c,h,cpp}" --line-number -F "%s"' % input_str
        if rel_path:
            args += " " + rel_path

        if not os.path.exists(".gitignore"):
            args += ' -g "!intermediates/" -g "!build/" -g "!Build/" -g "!ThirdParty/"'
        for x in exclude:
            args += ' -g "!%s"' % x

        args += " | peco"
        print2(args, color="cyan")
        out = get_output(args, shell=True).strip()
        if out:
            file, line_number, *_ = out.split(":")
            line_number = int(line_number)
            print("Goto: %s: %d" % (file, line_number))
            open_in_vscode(file, line_number, vscode_executable=os.environ.get['VSCODE_EXECUTABLE'])


if __name__ == "__main__":
    grep(src_dir=os.environ['GIT_REPO'], exclude=os.environ['_EXCLUDE'].split())
