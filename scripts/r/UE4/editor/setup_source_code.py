from _shutil import *
from _nvpack import *
from _appmanager import choco_install

# choco_install('directx')

# TODO: install vs2017 C++ and C#

try:
    setup_nvpack(r'{{NVPACK_ROOT}}')
except:
    print2('WARNING: NVPACK not found.')

chdir(r'{{UE_SOURCE}}')

if not exists('UE4.sln'):
    if exists('Setup.bat'):
        call_echo('Setup.bat')

    choco_install('netfx-4.6.2-devpack')

    call_echo('GenerateProjectFiles.bat -2017')
