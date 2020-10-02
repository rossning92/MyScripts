from _shutil import *
from _nvpack import *
from _appmanager import choco_install

choco_install('directx')

# TODO: install vs2017 C++ and C#

try:
    setup_nvpack(r"{{NVPACK_ROOT}}")
except:
    print2("WARNING: NVPACK not found.")

cd(r"{{UE_SOURCE}}")

if not exists("UE4.sln"):
    if exists("Setup.bat"):

        # Remove UnrealVersionSelector
        with open("Setup.bat") as f:
            s = f.read().replace(
                r".\Engine\Binaries\Win64\UnrealVersionSelector-Win64-Shipping.exe /register",
                "",
            )
        with open("Setup2.bat", "w") as f:
            f.write(s)
        call_echo("Setup2.bat")

    choco_install("netfx-4.6.2-devpack")

    call_echo("GenerateProjectFiles.bat -2017")
