import glob
import os

from _android import adb_install, get_pkg_name_apk, setup_android_env, start_app
from _script import get_variable
from _shutil import call_highlight, cd, find_newest_file, mkdir, print2

from build_cpp_modules import build_cpp_modules

setup_android_env()


OUT_DIR = "/tmp"


def build_uproject(project_dir, out_dir=None, compile_cpp=False):
    engine_source = get_variable("UE_SOURCE")
    print2("Engine: %s" % engine_source)

    cd(project_dir)

    project_file = glob.glob(os.path.join(project_dir, "*.uproject"))[0]
    print2("Project File: %s" % project_file)

    if out_dir is None:
        project_name = os.path.splitext(os.path.basename(project_file))[0]
        out_dir = OUT_DIR + "/%s" % project_name

    # Build C++ module?
    if compile_cpp:
        build_cpp_modules(project_dir)

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
    out_dir = build_uproject(
        project_dir=r"{{UE4_PROJECT_DIR}}", compile_cpp=bool("{{_COMPILE_CPP}}")
    )

    if "{{_INSTALL}}":
        apk = find_newest_file(out_dir + "/**/*.apk")
        adb_install(apk)

        pkg = get_pkg_name_apk(apk)
        start_app(pkg)
        # logcat(pkg)
