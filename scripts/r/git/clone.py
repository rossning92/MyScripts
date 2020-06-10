from _shutil import *
from _script import *


mkdir("~/Projects")
chdir("~/Projects")

folder = os.path.basename("{{GIT_URL}}")
folder = folder.rstrip(".git")

if not exists(folder):
    call("git clone %s --depth=1" % "{{GIT_URL}}")

set_variable("GIT_REPO", os.path.realpath(folder))

shell_open(folder)
