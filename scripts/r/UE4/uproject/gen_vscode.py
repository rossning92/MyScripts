from _shutil import *
from _android import *
from _script import get_variable


cd(r"{{UE_SOURCE}}")

project_file = find_file(os.path.join(r"{{UE4_PROJECT_DIR}}", "*.uproject"))


call_echo('GenerateProjectFiles.bat "%s" -Game -VSCode' % project_file)
