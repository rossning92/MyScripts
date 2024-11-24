import os

from utils.menu.logmenu import LogMenu

LogMenu(
    files=[os.path.join(os.environ["MY_DATA_DIR"], "MyScripts.log")],
    filter=" (I|W|E) .*",
).exec()
