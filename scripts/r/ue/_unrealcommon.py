import os
import re
import subprocess

from utils.android import (
    install_cmdline_tools,
    setup_android_env,
)


def get_unreal_source_version():
    version_file = os.path.join(
        os.environ["UE_SOURCE"],
        "Engine",
        "Source",
        "Runtime",
        "Launch",
        "Resources",
        "Version.h",
    )
    if not os.path.exists(version_file):
        raise Exception("Cannot find Version.h")
    with open(version_file, "r", encoding="utf-8") as f:
        s = f.read()

    match = re.findall(r"#define\s+ENGINE_(?:MAJOR|MINOR|PATCH)_VERSION\s+(\d+)", s)
    if not match:
        raise Exception("Cannot locate version in Version.h")
    version_str = f"{match[0]}.{match[1]}.{match[2]}"
    return version_str


def setup_ue_android_env():
    ue_version = get_unreal_source_version()
    if ue_version.startswith("5"):
        install_cmdline_tools(version="8.0")
        setup_android_env(jdk_version="11.0")  # for UE5.3+
        # subprocess.check_call(
        #     rf"{os.environ['UE_SOURCE']}\Engine\Extras\Android\SetupAndroid.bat",
        #     shell=True,
        # )
    elif ue_version.startswith("4.27"):
        setup_android_env(ndk_version="21.1.6352462", build_tools_version="28.0.3")
        subprocess.check_call(
            [
                "sdkmanager",
                "platform-tools",
                "platforms;android-28",
                "build-tools;28.0.3",
                "cmake;3.10.2.4988404",
                "ndk;21.1.6352462",
            ],
            shell=True,
        )
    else:
        raise Exception(f"Unknown Unreal Engine version: {ue_version}")
