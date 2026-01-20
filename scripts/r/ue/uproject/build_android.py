# https://dev.epicgames.com/documentation/en-us/unreal-engine/how-to-set-up-android-sdk-and-ndk-for-your-unreal-engine-development-environment

import glob
import os
import shutil
import subprocess

from _shutil import cd, confirm, find_newest_file, mkdir, print2
from _unrealcommon import setup_ue_android_env
from build_cpp_modules import build_cpp_modules
from utils.android import (
    adb_install,
    get_pkg_name_apk,
    start_app,
)
from utils.logger import setup_logger

out_dir_root = os.environ["UE_ANDROID_OUT_DIR"]


def build_uproject(
    ue_source, project_dir, out_dir=None, compile_cpp=False, clean=False
):
    print2("Engine: %s" % ue_source)

    cd(project_dir)

    if clean and confirm("Clean project?"):
        shutil.rmtree("Binaries")
        shutil.rmtree("Build")
        shutil.rmtree("Intermediate")
        shutil.rmtree("DerivedDataCache")
        shutil.rmtree("Saved")

    project_file = glob.glob(os.path.join(project_dir, "*.uproject"))[0]
    project_name = os.path.splitext(os.path.basename(project_file))[0]
    print2("Project File: %s" % project_file)

    if out_dir is None:
        out_dir = os.path.join(out_dir_root, project_name)

    # Build C++ module?
    if compile_cpp:
        build_cpp_modules(project_dir)

    # UE4 Automation Tool
    mkdir(out_dir)
    subprocess.check_call(
        [
            r"%s\Engine\Build\BatchFiles\RunUAT.bat" % ue_source,
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
        ]
    )

    # Copy the apk file to the output directory
    # apk_file = list(glob.glob(os.path.join(out_dir, "**", "*.apk"), recursive=True))[0]
    # os.rename(apk_file, os.path.join(out_dir, os.path.basename(out_dir) + ".apk"))

    return out_dir


if __name__ == "__main__":
    setup_logger()

    setup_ue_android_env()

    # run_script("r/ue/kill_editor.cmd")

    # TODO: no need this after UE5?

    out_dir = build_uproject(
        ue_source=os.environ["UE_SOURCE"],
        project_dir=os.environ["UE_PROJECT_DIR"],
        compile_cpp=bool(os.environ.get("UE_BUILD_ANDROID_COMPILE_CPP")),
        clean=bool(os.environ.get("UE_BUILD_ANDROID_CLEAN_BUILD")),
    )

    if os.environ.get("_INSTALL"):
        apk = find_newest_file(out_dir + "/**/*.apk")
        adb_install(apk)

        pkg = get_pkg_name_apk(apk)
        start_app(pkg)
        # logcat(pkg)
