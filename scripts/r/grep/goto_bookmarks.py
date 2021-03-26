from _grep import *
import yaml
import json
from _script import *


def parse_bookmarks(file):  # parse .md file
    with open(file, encoding="utf-8") as f:
        lines = f.readlines()

    lines.append("name: <FOR EVALUATING LAST VALUE>")

    bookmarks = []
    cur_vals = {}
    vars = get_all_variables()
    vars = {k: v[0] for k, v in vars.items()}
    for line in lines:
        line = line.rstrip("\n").rstrip("\r")

        match = re.match(r"^(name|kw|path)\s*:\s*(.*)", line)
        if match:
            key = match.group(1)
            val = match.group(2)

            if key == "path":  # `path` should be a list

                val = val.split("|")
                val = [x.strip() for x in val]

                # Translate path
                val = [x.format(**vars) for x in val]

            if key == "name":  # Store last parsed bookmark
                if "name" in cur_vals:  # not empty

                    bookmarks.append(cur_vals)
                    cur_vals = {
                        k: v for k, v in cur_vals.items() if k == "path"
                    }  # keep only `path` value

            cur_vals[key] = val

    return bookmarks


if __name__ == "__main__":
    bookmarks = []
    for bm in ["../../../data/grep/*.md", "bookmarks.md"]:
        for f in glob.glob(bm):
            f = os.path.abspath(f)
            bookmarks += parse_bookmarks(f)

    show_bookmarks(bookmarks=bookmarks)
