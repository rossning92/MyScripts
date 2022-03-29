import os

from _android import setup_android_env
from _appmanager import choco_install
from _shutil import call_echo, cd, print2, wait_key

from _nvpack import setup_nvpack

if __name__ == "__main__":
    choco_install("directx")

    # TODO: No need this after UE5.25?
    # setup_android_env()

    # TODO: install vs2017 C++ and C#

    cd(r"{{UE_SOURCE}}")

    if os.path.exists(
        r"Engine\Extras\Android\SetupAndroid.bat"
    ):  # NVPACK is deprecated for 5.25+
        call_echo(r"Engine\Extras\Android\SetupAndroid.bat")
    else:
        try:
            setup_nvpack(r"{{NVPACK_ROOT}}")
        except:
            print2("WARNING: NVPACK not found.")

    if os.path.exists(r"Engine\Extras\Redist\en-us\UE4PrereqSetup_x64.exe"):
        if wait_key("press y to install UE4PrereqSetup_x64.exe") != "y":
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

        choco_install("netfx-4.6.2-devpack")

        # call_echo("GenerateProjectFiles.bat -2017")
        call_echo("GenerateProjectFiles.bat")
