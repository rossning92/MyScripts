import os

from utils.menu.logviewer import LogViewerMenu

LogViewerMenu(
    files=[os.path.join(os.environ["MY_DATA_DIR"], "MyScripts.log")], filter=" (I|W|E) .*"
).exec()
