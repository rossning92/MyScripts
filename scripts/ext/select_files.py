import glob
import os

from _term import Menu

files = glob.glob(os.path.join("**", "*"), recursive=True)
menu = Menu(items=files)
menu.exec()
