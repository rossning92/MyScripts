from _shutil import *
from r.web.webscreenshot import webscreenshot


def gen_code_image(s, out_file, line_no=True, mark=[], debug=False):
    from urllib.parse import quote

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
    file = get_files()[0]

    out_dir = os.path.join(os.path.dirname(file), "out")
    mkdir(out_dir)

    with open(file, encoding="utf-8", newline="\n") as f:
        s = f.read()

    if 0: # Debug
        out_file = os.path.join(
            out_dir, os.path.splitext(os.path.basename(file))[0] + ".png",
        )
        gen_code_image(s, out_file, debug=True)

    else:
        parts = s.split("\n\n")
        for i in range(len(parts)):
            s = "\n\n".join(parts[0 : i + 1])

            out_file = os.path.join(
                out_dir,
                os.path.splitext(os.path.basename(file))[0] + ("-%02d.png" % (i + 1)),
            )

            gen_code_image(s, out_file)
