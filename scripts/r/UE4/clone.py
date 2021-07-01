from _shutil import *
from _script import *

VERSION = "{{UE4_BRANCH}}" if "{{UE4_BRANCH}}" else "4.25"
proj_dir = os.path.realpath("/Projects/UE" + VERSION)

if "{{_OVR_BRANCH}}":
    url = "https://github.com/Oculus-VR/UnrealEngine.git"
    proj_dir += "-OVR"
else:
    url = "https://github.com/EpicGames/UnrealEngine.git"


set_variable("UE_SOURCE", proj_dir)
make_and_change_dir(proj_dir)

call_echo(f"git clone -b {VERSION} --single-branch {url} --depth 1 .")
