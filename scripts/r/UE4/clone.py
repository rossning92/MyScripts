import os

from _script import set_variable
from _shutil import call_echo, make_and_change_dir

if __name__ == "__main__":
    branch = "{{UE4_BRANCH}}" if "{{UE4_BRANCH}}" else "4.25"
    proj_dir = os.path.realpath("/Projects/UE" + branch)

    if "{{_OVR_BRANCH}}":
        url = "https://github.com/Oculus-VR/UnrealEngine.git"
        proj_dir += "-OVR"
    else:
        url = "https://github.com/EpicGames/UnrealEngine.git"

    set_variable("UE_SOURCE", proj_dir)
    make_and_change_dir(proj_dir)

    call_echo(
        f"git clone -b {branch} --single-branch {url} --single-branch --filter=blob:none ."
    )
