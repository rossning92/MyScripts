from _shutil import *
from _nvpack import *
from _android import *

try:
    setup_nvpack(r"{{NVPACK_ROOT}}")
except:
    print2("WARNING: NVPACK not found.")
    setup_android_env()

os.environ["DATA_CACHE_DIR"] = r"C:\UE4-DataCache"

chdir(r"{{UE_SOURCE}}\Engine\Binaries\Win64")

# set UE-SharedDataCachePath=%DATA_CACHE_DIR%
# start UE4Editor.exe -ddc=noshared
try:
    call2("taskkill /f /im UE4Editor.exe")
except:
    pass

call2("start UE4Editor.exe")
