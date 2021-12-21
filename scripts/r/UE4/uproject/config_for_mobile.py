from _shutil import *
import stat


def _add_value(ini_file, section, kvps):
    print("== " + ini_file + " ==")
    if os.path.exists(ini_file):
        with open(ini_file) as f:
            lines = f.readlines()
    else:
        lines = []

    lines = [line.rstrip() for line in lines]

    # Only updated modified kvps
    kvps = [x for x in kvps if x not in lines]

    # Remove existing value
    for kvp in kvps:
        if not kvp:
            continue

        k, v = kvp.split("=")
        indices = [i for i in range(len(lines)) if lines[i].startswith(k + "=")]
        lines = [lines[i] for i in range(len(lines)) if i not in indices]

    # Find section
    try:
        i = lines.index(section)
        i += 1

    except ValueError:
        lines.append("")
        lines.append(section)
        i = len(lines)

    # Add value
    lines[i:i] = kvps
    print(section)
    print2("\n".join(kvps), color="green")

    # Save to file
    call2('attrib -r "%s"' % ini_file)
    os.makedirs(os.path.dirname(ini_file), exist_ok=True)
    with open(ini_file, "w") as f:
        f.write("\n".join(lines))

    print()


def config_uproject(project_dir, vulkan=True, multiview=True, msaa=4):
    os.chdir(project_dir)

    _add_value(
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

    _add_value(
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

    # _add_value(
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
