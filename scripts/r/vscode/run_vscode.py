import os

from _editor import open_in_editor

root_folder = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../../..")
open_in_editor(root_folder)
