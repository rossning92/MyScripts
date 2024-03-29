import glob
import os

from _ue4 import update_config


def config_uproject(
    project_dir,
    vulkan=True,
    multiview=True,
    msaa=4,
    openxr=True,
    tonemapsubpass=False,
    update_package_name=False,
    is_ue5=True,
):
    os.chdir(project_dir)

    project_file = glob.glob(os.path.join(project_dir, "*.uproject"))[0]
    project_name = os.path.splitext(os.path.basename(project_file))[0]

    kvp = [
        "+PackageForOculusMobile=Quest2",
        "bSupportsVulkan=%s" % str(vulkan),
        "bBuildForES2=False",
        "bBuildForES31=%s" % str(not vulkan),
        "bPackageDataInsideApk=True",
        f"MinSDKVersion={32 if is_ue5 else 23}",
        f"TargetSDKVersion={32 if is_ue5 else 25}",
        "bFullScreen=True",
        "bRemoveOSIG=True",
        "bBuildForArmV7=False",
        "bBuildForArm64=True",
    ]
    if update_package_name:
        kvp.append(
            f"PackageName=com.company.{project_name.lower()}{'vk' if vulkan else 'gl'}"
        )
    update_config(
        "Config/DefaultEngine.ini",
        "[/Script/AndroidRuntimeSettings.AndroidRuntimeSettings]",
        kvp,
    )

    update_config(
        "Config/DefaultEngine.ini",
        "[/Script/Engine.RendererSettings]",
        [
            "r.MobileHDR=False",
            # "r.MSAA.CompositingSampleCount=%d" % msaa,
            f"r.MSAACount={msaa}" if is_ue5 else f"r.MobileMSAA={msaa}",
            "vr.MobileMultiView=%s" % str(multiview),
            "vr.MobileMultiView.Direct=%s" % str(multiview),
        ],
    )

    if openxr:
        # UE5+
        update_config(
            "Config/DefaultEngine.ini",
            "[/Script/OculusHMD.OculusHMDRuntimeSettings]",
            ["XrApi=OVRPluginOpenXR"],
        )

    console_variables = []
    if tonemapsubpass:
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
