import os


def create_gitignore(dirpath: str):
    gitignore_path = os.path.join(dirpath, ".gitignore")
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, "w") as f:
            f.write("*")
