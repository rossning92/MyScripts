import os

from _appmanager import choco_install
from _shutil import call_echo, cd

if __name__ == "__main__":
    choco_install("directx")


    # TODO: install vs2019 C++ and C#

    cd(r"{{UE_SOURCE}}")

    if os.path.exists(r"Engine\Extras\Redist\en-us\UE4PrereqSetup_x64.exe"):
        call_echo(
            r"cmd /c start /wait Engine\Extras\Redist\en-us\UE4PrereqSetup_x64.exe /quiet"
        )

    if not os.path.exists("UE4.sln"):
        if os.path.exists("Setup.bat"):

            # Remove UnrealVersionSelector
            with open("Setup.bat") as f:
                s = f.read().replace(
                    r".\Engine\Binaries\Win64\UnrealVersionSelector-Win64-Shipping.exe /register",
                    "",
                )
            with open("Setup.NoVersionSelector.bat", "w") as f:
                f.write(s)
            call_echo("Setup.NoVersionSelector.bat")

        # choco_install("netfx-4.6.2-devpack")

        # call_echo("GenerateProjectFiles.bat -2017")
        call_echo("GenerateProjectFiles.bat")
