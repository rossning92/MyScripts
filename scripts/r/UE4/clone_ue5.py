from _shutil import *
from _script import *

branch = "ue5-early-access"
proj_dir = os.path.realpath("/Projects/" + branch)

url = "https://github.com/EpicGames/UnrealEngine.git"


set_variable("UE_SOURCE", proj_dir)
make_and_change_dir(proj_dir)

call_echo(f"git clone -b {branch} --single-branch {url} --depth 1 .")
