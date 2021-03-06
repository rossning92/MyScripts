from _shutil import *
from _nvpack import *
from _android import *

uproject_dir = r"{{UE4_PROJECT_DIR}}"

# No need for NVPACK in UE4.25+
# try:
#     setup_nvpack(r"{NVPACK_ROOT}")
# except:
#     print2("WARNING: NVPACK not found.")

setup_android_env()

os.environ["DATA_CACHE_DIR"] = r"C:\UE4-DataCache"

cd(r"{{UE_SOURCE}}\Engine\Binaries\Win64")

# set UE-SharedDataCachePath=%DATA_CACHE_DIR%
# start UE4Editor.exe -ddc=noshared


if os.path.exists("UnrealEditor.exe"):  # UE5
    call_echo("taskkill /im UnrealEditor.exe", check=False)
    args = ["UnrealEditor.exe"]
else:
    call_echo("taskkill /im UE4Editor.exe", check=False)
    args = ["UE4Editor.exe"]


if uproject_dir:
    args.append(find_file(os.path.join(uproject_dir, "*.uproject")))

print2("Starting UE4Editor...")
start_process(args)
sleep(2)
