import os

from _ue4 import update_config


def config_uproject(project_dir, vulkan=True, multiview=True, msaa=4):
    os.chdir(project_dir)

    update_config(
        "Config/DefaultEngine.ini",
        "[/Script/AndroidRuntimeSettings.AndroidRuntimeSettings]",
        [
            "+PackageForOculusMobile=Quest",
            "+PackageForOculusMobile=Quest2",
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
            "r.MobileMSAA=%d" % msaa,
            "r.MSAA.CompositingSampleCount=%d" % msaa,
            "vr.MobileMultiView=%s" % str(multiview),
            "vr.MobileMultiView.Direct=%s" % str(multiview),
        ],
    )

    # update_config(
    #     "Saved/Config/Windows/Game.ini",
    #     "[/Script/UnrealEd.ProjectPackagingSettings]",
    #     [
    #         "BuildConfiguration=PPBC_Shipping",
    #     ],
    # )


if __name__ == "__main__":
    config_uproject(
        r"{{UE4_PROJECT_DIR}}",
        vulkan=not bool("{{_GL}}"),
        multiview=not bool("{{_NO_MULTIVIEW}}"),
    )
