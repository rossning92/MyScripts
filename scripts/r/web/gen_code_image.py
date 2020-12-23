from _cache import *
from _shutil import *
from r.web.webscreenshot import webscreenshot
import argparse


@file_cache
def gen_code_image_from_file(file, out_file, mtime=None):
    with open(file, "r", encoding="utf-8") as f:
        s = f.read()
        gen_code_image(s, out_file)


def gen_code_image(s, out_file, line_no=True, debug=False):
    from urllib.parse import quote

    ranges = [[m.start(), m.end()] for m in re.finditer("`.*?`", s)]
    s = s.replace("`", "")

    javascript = "setCode('%s'); " % quote(s)

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
        html_file=root + "/codeeditor.html",
        out_file=out_file,
        javascript=javascript,
        debug=debug,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str, help="input source file")
    args = parser.parse_args()

    file = args.file

    out_dir = os.path.join(os.path.dirname(file), "out")
    mkdir(out_dir)

    with open(file, encoding="utf-8", newline="\n") as f:
        s = f.read()

    if 0:  # Debug
        out_file = os.path.join(
            out_dir, os.path.splitext(os.path.basename(file))[0] + ".png",
        )
        gen_code_image(s, out_file, debug=True)

    else:
        out_file = os.path.join(
            out_dir, os.path.splitext(os.path.basename(file))[0] + ".png",
        )

        gen_code_image(s, out_file)

        # parts = s.split("\n\n")
        # for i in range(len(parts)):
        #     s = "\n\n".join(parts[0 : i + 1])

