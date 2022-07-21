import os

from _editor import open_in_vscode

if __name__ == "__main__":
    project_file = os.path.join(
        os.environ["UE_PROJECT_DIR"], "Config", "DefaultEngine.ini"
    )
    open_in_vscode(project_file)
