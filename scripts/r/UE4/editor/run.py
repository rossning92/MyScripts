from _shutil import *
from _nvpack import *

setup_nvpack(r'{{NVPACK_ROOT}}')

os.environ['DATA_CACHE_DIR'] = r'C:\UE4-DataCache'

chdir(r'{{UE_SOURCE}}\Engine\Binaries\Win64')

# set UE-SharedDataCachePath=%DATA_CACHE_DIR%
# start UE4Editor.exe -ddc=noshared
Popen('UE4Editor.exe')
