from _shutil import *
from _script import *
from _editor import open_in_vscode

mkdir("~/Projects")
chdir("~/Projects")

folder = os.path.basename("{{GIT_URL}}")
folder = re.sub(".git$", "", folder)

if not exists(folder):
    call("git clone %s --depth=1" % "{{GIT_URL}}")

set_variable("GIT_REPO", os.path.realpath(folder))

open_in_vscode(folder)
