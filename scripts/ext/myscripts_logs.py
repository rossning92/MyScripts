import os

from utils.menu.logmenu import LogMenu

LogMenu(
    files=[os.path.join(os.environ["MY_DATA_DIR"], "myscripts.log")],
    filter=" (I|W|E) .*",
).exec()
