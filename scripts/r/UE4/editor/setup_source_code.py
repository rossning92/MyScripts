from _shutil import *
from _nvpack import *

setup_nvpack(r'{{NVPACK_ROOT}}')

chdir(r'{{UE_SOURCE}}')

call('cmd /c Setup.bat')

call('cmd /c GenerateProjectFiles.bat -2017')
