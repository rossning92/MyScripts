import os

from _shutil import call_echo, print2
from _template import render_template_file

import vcpkg

# BUILD_LIB = "{{BUILD_LIB}}" == "Y"
template_file = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "CMakeLists.template.txt"
)


def cmake_build(project_dir, project_name=None):
    print2("Project dir: %s" % project_dir)

    if project_name is None:
        project_name = os.path.basename(project_dir).replace(" ", "_")

    # Create CMakeList.txt
    cmakelist_file = os.path.join(project_dir, "CMakeLists.txt")
    if not os.path.exists(cmakelist_file):
        render_template_file(
            template_file, cmakelist_file, {"PROJECT_NAME": project_name},
        )

    # Add cmake to PATH
    os.environ["PATH"] = r"C:\Program Files\CMake\bin" + os.pathsep + os.environ["PATH"]

    # shutil.rmtree("build")

    # Config the project
    args = ["cmake"]
    if os.path.exists(vcpkg.VCPKG_ROOT):
        toolchain_file = (
            "%s/scripts/buildsystems/vcpkg.cmake" % vcpkg.VCPKG_ROOT.replace("\\", "/")
        )
        assert os.path.exists(toolchain_file)
        args += [
            "-DCMAKE_TOOLCHAIN_FILE=%s" % toolchain_file,
        ]
    args += [
        "-S",
        ".",  # path-to-source (required)
        "-B",
        "build",  # path-to-build (required)
        # "-G", "Visual Studio 16 2019",
        # "-T", "host=x86",
        # "-A", "win32"
    ]
    call_echo(args, cwd=project_dir)

    # Build the project
    call_echo(
        [
            "cmake",
            "--build",
            "build",
            # "--config", "Release"
        ],
        cwd=project_dir,
    )


# Run the executable
# call_echo(".\\build\\Release\\main.exe")
# shell_open("build\\thread.sln")

# if __name__ == "__main__":
#     if r"{{CMAKE_PROJECT_DIR}}":
#         project_dir = r"{{CMAKE_PROJECT_DIR}}"
#     else:
#         project_dir = os.environ["_CUR_DIR"]
#         set_variable("CMAKE_PROJECT_DIR", project_dir)

#     # Remove cmake cache
#     # if "{{CMAKE_REMOVE_CACHE}}" == "Y":
#     #     if os.path.exists("CMakeCache.txt"):
#     #         os.remove("CMakeCache.txt")

#     cmake_build(project_dir=project_dir)
