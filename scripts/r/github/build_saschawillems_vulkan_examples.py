from _android import setup_android_env
from _cmake import setup_cmake
from _git import git_clone
from _shutil import call_echo, cd, shell_open

# Ninja is required
# run_elevated("choco install ninja -y")

setup_cmake()
setup_android_env()

git_clone("https://github.com/SaschaWillems/Vulkan")

cd("build", auto_create_dir=True)
call_echo('cmake -G "Visual Studio 16 2019" -A x64 ..')
shell_open('vulkanExamples.sln')
