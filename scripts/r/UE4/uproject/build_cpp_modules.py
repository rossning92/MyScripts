import glob
import os

from _script import get_variable
from _shutil import call_echo, cd, print2


def build_cpp_modules(project_dir):
    engine_source = get_variable("UE_SOURCE")
    print2("Engine: %s" % engine_source)

    cd(project_dir)

    project_file = glob.glob(os.path.join(project_dir, "*.uproject"))[0]
    print2("Project File: %s" % project_file)

    unreal_build_tools = (
        r"%s\Engine\Binaries\DotNET\UnrealBuildTool.exe" % engine_source
    )
    if not os.path.exists(unreal_build_tools):
        # Path changes in UE5
        unreal_build_tools = (
            r"%s\Engine\Binaries\DotNET\UnrealBuildTool\UnrealBuildTool.exe"
            % engine_source
        )

    # Build C++ modules
    call_echo(
        [
            unreal_build_tools,
            "Development",
            "Win64",
            "-Project=%s" % project_file,
            "-TargetType=Editor",
            "-Progress",
            # "-NoEngineChanges",
            # "-NoHotReloadFromIDE",
        ]
    )


if __name__ == "__main__":
    build_cpp_modules(project_dir=r"{{UE_PROJECT_DIR}}")
