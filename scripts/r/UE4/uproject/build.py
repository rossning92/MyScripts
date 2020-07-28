from _shutil import *
from _android import *
from _script import get_variable

setup_android_env()


def build_uproject(project_dir, out_dir=None):
    cd(project_dir)

    project_file = glob.glob(os.path.join(project_dir, "*.uproject"))[0]
    print(project_file)

    if out_dir is None:
        project_name = os.path.splitext(os.path.basename(project_dir))[0]
        out_dir = "/tmp/%s" % project_name

    mkdir(out_dir)
    call_echo(
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
            "-clientconfig=Shipping",
            "-utf8output",
            "-compile",
        ]
    )


if __name__ == "__main__":
    build_uproject(project_dir=r"{{UE4_PROJECT_DIR}}")
