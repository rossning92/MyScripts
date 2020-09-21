from _shutil import *
from r.web.webscreenshot import webscreenshot


def code(file, line_no=True, mark=[], debug=False):
    from urllib.parse import quote

    out_dir = os.path.join(os.path.dirname(file), "out")
    mkdir(out_dir)
    out_file = os.path.join(
        out_dir, os.path.splitext(os.path.basename(file))[0] + ".png"
    )

    with open(file, encoding="utf-8") as f:
        s = f.read()

    javascript = "setCode('%s'); " % quote(s)

    mark_group = list(zip(*(iter(mark),) * 4))
    for x in mark_group:
        javascript += "markText(%d, %d, %d, %d); " % (x[0], x[1], x[2], x[3],)

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
    code(get_files()[0])
