from _shutil import *
from _nvpack import *

# TODO: install DirectX
run_elevated('choco install directx -y')

# TODO: install vs2017 C++ and C#


setup_nvpack(r'{{NVPACK_ROOT}}')

chdir(r'{{UE_SOURCE}}')

if exists('Setup.bat'):
    call('cmd /c Setup.bat')

call('cmd /c GenerateProjectFiles.bat -2017')
