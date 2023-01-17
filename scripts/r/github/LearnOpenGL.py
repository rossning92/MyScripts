import os

from _cpp import setup_cmake
from _editor import open_in_vscode
from _git import git_clone
from _shutil import call_echo

if __name__ == "__main__":
    repo_dir = git_clone("https://github.com/JoeyDeVries/LearnOpenGL")
    open_in_vscode(repo_dir)

    if os.environ.get("_BUILD"):
        setup_cmake()

        os.makedirs("build", exist_ok=True)
        call_echo(
            ["cmake", "-G" "Visual Studio 16 2019", ".."], cwd="build", shell=True
        )
        call_echo("build\\LearnOpenGL.sln", check=False, shell=True)
