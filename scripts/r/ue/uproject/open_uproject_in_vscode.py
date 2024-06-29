import os

from utils.editor import open_code_editor

if __name__ == "__main__":
    project_file = os.path.join(
        os.environ["UE_PROJECT_DIR"], "Config", "DefaultEngine.ini"
    )
    open_code_editor(project_file)
