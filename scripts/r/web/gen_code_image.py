from _cache import *
from _shutil import *
from web.webscreenshot import webscreenshot
import argparse


def gen_code_image_from_file(file, out_file, **kwargs):
    with open(file, "r", encoding="utf-8", newline="\n") as f:
        s = f.read().replace("\r", "")
        gen_code_image(s, out_file, **kwargs)


def gen_code_image(
    s,
    out_file,
    line_no=True,
    debug=False,
    lang=None,
    size=None,
    jump_line=None,
    fontsize=None,
    mark_line=None,
    bg=None,
):
    from urllib.parse import quote

    s = s.replace("\\`", "\u2022")
    ranges = [[m.start(), m.end()] for m in re.finditer("`.*?`", s)]
    s = s.replace("`", "")
    s = s.replace("\u2022", "`")

    # Source code content
    javascript = "setCode('%s', '%s');" % (quote(s), lang)

    # Highlight code
    for i in range(len(ranges)):
        javascript += "markText(%d, %d);" % (
            ranges[i][0] - i * 2,
            ranges[i][1] - i * 2 - 2,
        )

    # Line numbers
    javascript += "showLineNumbers(%s);" % ("true" if line_no else "false")

    # Font size
    if fontsize is not None:
        javascript += "setFontSize(%g);" % fontsize

    # Size
    if size is not None:
        javascript += "setSize(%d, %d);" % (size[0], size[1])

    # Jump to line
    if jump_line is not None:
        javascript += "jumpToLine(%d);" % jump_line

    # Mark line
    if mark_line:
        if isinstance(mark_line, (int, float)):
            mark_line = [mark_line]
        for i in mark_line:
            javascript += "markLine(%d);" % i

    root = get_script_root() + "/r/web/_codeeditor"
    npm_install(root)

    webscreenshot(
        html_file=root + "/code_editor.html",
        out_file=out_file,
        javascript=javascript,
        debug=debug,
    )

    if bg is not None:
        from PIL import Image

        img = Image.open(out_file, "r")
        img_w, img_h = img.size
        background = Image.open(bg, "r")
        bg_w, bg_h = background.size
        offset = ((bg_w - img_w) // 2, (bg_h - img_h) // 2)
        background.paste(img, offset)
        background.save(out_file)


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

