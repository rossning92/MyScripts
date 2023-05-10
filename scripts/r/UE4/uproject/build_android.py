import glob
import os
import shutil

from _android import (
    adb_install,
    get_pkg_name_apk,
    setup_android_env,
    start_app,
    install_cmdline_tools,
)
from _script import run_script
from _shutil import (
    call_highlight,
    cd,
    confirm,
    find_newest_file,
    mkdir,
    print2,
    setup_logger,
)
import subprocess
from build_cpp_modules import build_cpp_modules
from _unrealcommon import get_unreal_source_version

out_dir_root = os.environ.get("UE_ANDROID_OUT_DIR", "/tmp")


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
    print2("Project File: %s" % project_file)

    if out_dir is None:
        project_name = os.path.splitext(os.path.basename(project_file))[0]
        out_dir = out_dir_root + "/%s" % project_name

    # Build C++ module?
    if compile_cpp:
        build_cpp_modules(project_dir)

    # UE4 Automation Tool
    mkdir(out_dir)
    call_highlight(
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
        ],
        highlight={r"\b(warning|WARNING):": "yellow", r"\b(error|ERROR):": "RED"},
    )
    return out_dir


if __name__ == "__main__":
    setup_logger()

    ue_version = get_unreal_source_version()
    if ue_version[0] == "5":
        install_cmdline_tools(version="8.0")
        setup_android_env()
        # subprocess.check_call(
        #     rf"{os.environ['UE_SOURCE']}\Engine\Extras\Android\SetupAndroid.bat",
        #     shell=True,
        # )
    elif ue_version == "4.27":
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

    # run_script("r/UE4/kill_editor.cmd")

    # TODO: no need this after UE5?

    out_dir = build_uproject(
        ue_source=os.environ["UE_SOURCE"],
        project_dir=os.environ["UE_PROJECT_DIR"],
        compile_cpp=bool(os.environ.get("_COMPILE_CPP")),
        clean=bool(os.environ.get("_CLEAN")),
    )

    if os.environ.get("_INSTALL"):
        apk = find_newest_file(out_dir + "/**/*.apk")
        adb_install(apk)

        pkg = get_pkg_name_apk(apk)
        start_app(pkg)
        # logcat(pkg)
