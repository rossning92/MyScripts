from _grep import show_bookmarks
import yaml
import json
from _script import *


if __name__ == "__main__":
    vars = get_all_variables()
    vars = {k: v[0] for k, v in vars.items()}

    bookmarks = []
    for bm in ["../../../data/grep/*.yml", "bookmarks.yml"]:
        for file in glob.glob(bm):
            file = os.path.abspath(file)

            with open(file, "r") as f:
                data = yaml.load(f.read(), Loader=yaml.FullLoader)

            # Translate path
            for bookmark in data:
                bookmark["path"] = bookmark["path"].format(**vars)

            bookmarks += data

    show_bookmarks(bookmarks=bookmarks)
