from _cache import *
from _shutil import *
from r.web.webscreenshot import webscreenshot
import argparse


@file_cache
def gen_code_image_from_file(file, out_file, mtime=None):
    with open(file, "r", encoding="utf-8", newline="\n") as f:
        s = f.read()
        gen_code_image(s, out_file)


def gen_code_image(s, out_file, line_no=True, debug=False, lang=None):
    from urllib.parse import quote

    s = s.replace("\\`", "\u2022")
    ranges = [[m.start(), m.end()] for m in re.finditer("`.*?`", s)]
    s = s.replace("`", "")
    s = s.replace("\u2022", "`")

    javascript = "setCode('%s', '%s'); " % (quote(s), lang)

    # Highlight code
    for i in range(len(ranges)):
        javascript += (
            'editor.markText(editor.posFromIndex(%d), editor.posFromIndex(%d), {className: "highlight"});'
            % (ranges[i][0] - i * 2, ranges[i][1] - i * 2 - 2)
        )

    javascript += "showLineNumbers(%s); " % ("true" if line_no else "false")

    root = get_script_root() + "/r/web/_codeeditor"
    if not os.path.join(root, "node_modules"):
        call_echo("yarn")

    webscreenshot(
        html_file=root + "/code_editor.html",
        out_file=out_file,
        javascript=javascript,
        debug=debug,
    )


if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument("file", type=str, help="input source file")
    # args = parser.parse_args()
    # file = args.file

    files = get_files(cd=True)

    for file in files:
        out_dir = os.path.join(os.path.dirname(file), "out")
        mkdir(out_dir)

        _, ext = os.path.splitext(file)
        with open(file, encoding="utf-8", newline="\n") as f:
            s = f.read().replace("\r", "")

        out_file = os.path.join(
            out_dir, os.path.splitext(os.path.basename(file))[0] + ".png",
        )

        gen_code_image(s, out_file, lang=ext.lstrip("."))

