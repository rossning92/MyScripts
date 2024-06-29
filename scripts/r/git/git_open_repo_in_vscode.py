import os

from utils.editor import open_code_editor

if __name__ == "__main__":
    git_repo = os.environ["GIT_REPO"]
    if not os.path.exists(git_repo):
        raise Exception("Git repo does not exists.")

    open_code_editor(git_repo)
