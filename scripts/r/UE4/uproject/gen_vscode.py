import os

from _script import call_echo
from _shutil import cd, find_newest_file

if __name__ == "__main__":
    cd(r"{{UE_SOURCE}}")
    project_file = find_newest_file(os.path.join(r"{{UE4_PROJECT_DIR}}", "*.uproject"))
    call_echo('GenerateProjectFiles.bat "%s" -Game -VSCode' % project_file)
