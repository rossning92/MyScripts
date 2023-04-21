import os

from _ue4 import update_config


def config_uproject(project_dir, vulkan=True, multiview=True, msaa=4, openxr=True):
    os.chdir(project_dir)

    update_config(
        "Config/DefaultEngine.ini",
        "[/Script/AndroidRuntimeSettings.AndroidRuntimeSettings]",
        [
            "+PackageForOculusMobile=Quest2",
            "+PackageForOculusMobile=QuestPro",
            "bSupportsVulkan=%s" % str(vulkan),
            "bBuildForES2=False",
            "bBuildForES31=%s" % str(not vulkan),
            "bPackageDataInsideApk=True",
            "MinSDKVersion=23",
            "TargetSDKVersion=25",
            "bFullScreen=True",
            "bRemoveOSIG=True",
            "bBuildForArmV7=False",
            "bBuildForArm64=True",
        ],
    )

    update_config(
        "Config/DefaultEngine.ini",
        "[/Script/Engine.RendererSettings]",
        [
            "r.MobileHDR=False",
            # "r.MSAA.CompositingSampleCount=%d" % msaa,
            "r.MobileMSAA=%d" % msaa,  # UE4
            "r.MSAACount=%d" % msaa,  # UE5
            "vr.MobileMultiView=%s" % str(multiview),
            "vr.MobileMultiView.Direct=%s" % str(multiview),
        ],
    )

    if openxr:
        update_config(
            "Config/DefaultEngine.ini",
            "[/Script/OculusHMD.OculusHMDRuntimeSettings]",
            ["XrApi=OVRPluginOpenXR"],
        )

    console_variables = []
    console_variables.append("r.Mobile.TonemapSubpass=1")
    if console_variables:
        update_config(
            "Config/DefaultEngine.ini",
            "[ConsoleVariables]",
            console_variables,
        )


if __name__ == "__main__":
    config_uproject(
        r"{{UE_PROJECT_DIR}}",
        vulkan=not bool("{{_USE_GL}}"),
        multiview=not bool("{{_NO_MULTIVIEW}}"),
    )
