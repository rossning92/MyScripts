import os

from _android import setup_android_env
from _shutil import call_echo, cd, find_newest_file, print2, start_process

if __name__ == "__main__":
    # No need NVPACK for UE4.25+
    # try:
    #     setup_nvpack(os.environ["NVPACK_ROOT"])
    # except:
    #     print2("WARNING: NVPACK not found.")

    setup_android_env()

    # os.environ["DATA_CACHE_DIR"] = r"C:\UE4-DataCache"

    cd(os.path.join(os.environ["UE_SOURCE"], r"Engine\Binaries\Win64"))

    args = ["cmd", "/c", "start"]
    if os.path.exists("UnrealEditor.exe"):  # UE5
        call_echo("taskkill /f /im UnrealEditor.exe", check=False)
        args.append("UnrealEditor.exe")
    else:
        # set UE-SharedDataCachePath=%DATA_CACHE_DIR%
        # start UE4Editor.exe -ddc=noshared
        call_echo("taskkill /f /im UE4Editor.exe", check=False)
        args.append("UE4Editor.exe")

    uproject_dir = os.environ.get("UE_PROJECT_DIR")
    if uproject_dir:
        args.append(find_newest_file(os.path.join(uproject_dir, "*.uproject")))

    print2("Starting Unreal Editor...")
    call_echo(args)
