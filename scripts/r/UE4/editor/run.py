from _shutil import *
# import _setup_android_env; _setup_android_env.setup_android_env()
from _nvpack import *

setup_nvpack(r'{{NVPACK_ROOT}}')

os.environ['DATA_CACHE_DIR'] = r'C:\UE4-DataCache'

chdir(r'{{UE_SOURCE}}\Engine\Binaries\Win64')

# set UE-SharedDataCachePath=%DATA_CACHE_DIR%
# start UE4Editor.exe -ddc=noshared
try:
    call2('taskkill /f /im UE4Editor.exe')
except:
    pass

call2('start UE4Editor.exe')
