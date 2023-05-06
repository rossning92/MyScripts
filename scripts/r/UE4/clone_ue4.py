from _shutil import call_echo, make_and_change_dir

if __name__ == "__main__":
    branch = "{{UE4_BRANCH}}" if "{{UE4_BRANCH}}" else "4.27"
    make_and_change_dir(r"{{UE_SOURCE}}")

    if "{{_OVR_BRANCH}}":
        url = "https://github.com/Oculus-VR/UnrealEngine.git"
    else:
        url = "https://github.com/EpicGames/UnrealEngine.git"

    call_echo(
        f"git clone -b {branch} --single-branch {url} --single-branch --filter=blob:none ."
    )
