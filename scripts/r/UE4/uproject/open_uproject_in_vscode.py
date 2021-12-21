import os

from _editor import open_in_vscode

project_dir = r"{{UE4_PROJECT_DIR}}"
project_file = os.path.join(project_dir, "Config", "DefaultEngine.ini")
open_in_vscode(project_file)
