from _shutil import *
from _android import *
from _script import get_variable

setup_android_env()


OUT_DIR = "/tmp"


def build_uproject(project_dir, out_dir=None):
    engine_source = get_variable("UE_SOURCE")
    print2("Engine: %s" % engine_source)

    cd(project_dir)

    project_file = glob.glob(os.path.join(project_dir, "*.uproject"))[0]
    print2("Project File: %s" % project_file)

    if out_dir is None:
        project_name = os.path.splitext(os.path.basename(project_file))[0]
        out_dir = OUT_DIR + "/%s" % project_name

    # Build module?
    if False:
        call_echo(
            [
                r"%s\Engine\Binaries\DotNET\UnrealBuildTool.exe" % engine_source,
                "Development",
                "Win64",
                "-Project=%s" % project_file,
                "-TargetType=Editor",
                "-Progress",
                "-NoEngineChanges",
                "-NoHotReloadFromIDE",
            ]
        )

    # UE4 Automation Tool
    mkdir(out_dir)
    call_highlight(
        [
            r"%s\Engine\Build\BatchFiles\RunUAT.bat" % get_variable("UE_SOURCE"),
            "BuildCookRun",
            "-nocompileeditor",
            "-nop4",
            "-project=%s" % project_file,
            "-cook",
            "-stage",
            "-archive",
            "-archivedirectory=%s" % out_dir,
            "-package",
            # "-ue4exe=C:\Users\rossning92\Unreal Projects\UE4.25-OVR\Engine\Binaries\Win64\UE4Editor-Cmd.exe",
            "-pak",
            "-prereqs",  # Prerequisites installer
            "-nodebuginfo",
            "-targetplatform=Android",
            "-cookflavor=ASTC",
            "-build",
            "-CrashReporter",
            "-clientconfig=Development",
            "-utf8output",
            "-compile",
        ],
        highlight={r"\b(warning|WARNING):": "yellow", r"\b(error|ERROR):": "RED"},
    )
    return out_dir


if __name__ == "__main__":
    out_dir = build_uproject(project_dir=r"{{UE4_PROJECT_DIR}}")

    if "{{_INSTALL}}":
        apk = find_file(out_dir + "/**/*.apk")
        adb_install(apk)

        pkg = get_pkg_name_apk(apk)
        start_app(pkg)
        # logcat(pkg)
