from _shutil import *
from _nvpack import *

run_elevated('choco install directx -y')

# TODO: install vs2017 C++ and C#


setup_nvpack(r'{{NVPACK_ROOT}}')

chdir(r'{{UE_SOURCE}}')

if not exists('UE4.sln'):
    if exists('Setup.bat'):
        call_echo('Setup.bat')

    call_echo('GenerateProjectFiles.bat -2017')
