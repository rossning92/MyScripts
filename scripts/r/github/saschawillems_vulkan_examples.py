import os

from _android import setup_android_env
from _cpp import setup_cmake
from _editor import open_in_editor
from _git import git_clone
from _shutil import call_echo, cd, setup_logger, shell_open

if __name__ == "__main__":
    setup_logger()

    d = git_clone("https://github.com/SaschaWillems/Vulkan")

    if os.environ.get("_BUILD"):
        # Ninja is required
        # run_elevated("choco install ninja -y")

        setup_cmake()
        setup_android_env()

        cd("build", auto_create_dir=True)
        call_echo('cmake -G "Visual Studio 16 2019" -A x64 ..')
        shell_open("vulkanExamples.sln")
    else:
        open_in_editor(d)
