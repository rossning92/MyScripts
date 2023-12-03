import os

from _pkgmanager import install_package
from _shutil import call_echo, cd

if __name__ == "__main__":
    install_package("directx")

    # TODO: install vs2019 C++ and C#

    cd(os.environ["UE_SOURCE"])

    if os.path.exists(r"Engine\Extras\Redist\en-us\UE4PrereqSetup_x64.exe"):
        call_echo(
            r"cmd /c start /wait Engine\Extras\Redist\en-us\UE4PrereqSetup_x64.exe /quiet"
        )

    if not os.path.exists("UE4.sln"):
        if os.path.exists("Setup.bat"):
            call_echo("run_script r/ue/editor/SelectNoRegisterUEFileTypes.ahk")
            call_echo("Setup.bat")

        # install_package("netfx-4.6.2-devpack")

        # call_echo("GenerateProjectFiles.bat -2017")
        call_echo("GenerateProjectFiles.bat")
