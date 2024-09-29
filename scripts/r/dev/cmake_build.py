import os
import subprocess

import vcpkg
from _shutil import print2
from utils.template import render_template_file

template_file = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "CMakeLists.template.txt"
)


def cmake_build(project_dir=None, project_name=None, use_vcpkg=False):
    if project_dir is None:
        project_dir = os.getcwd()

    print2("Project dir: %s" % project_dir)

    if project_name is None:
        project_name = os.path.basename(project_dir).replace(" ", "_")

    # Create CMakeList.txt
    cmakelist_file = os.path.join(project_dir, "CMakeLists.txt")
    if not os.path.exists(cmakelist_file):
        render_template_file(
            template_file,
            cmakelist_file,
            {"PROJECT_NAME": project_name},
        )

    # Add cmake to PATH
    os.environ["PATH"] = r"C:\Program Files\CMake\bin" + os.pathsep + os.environ["PATH"]

    # shutil.rmtree("build")

    # Config the project
    args = ["cmake", "-DCMAKE_BUILD_TYPE=Release"]
    if use_vcpkg and os.path.exists(vcpkg.VCPKG_ROOT):
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
    ]
    if os.environ.get("_WIN32"):
        args += ["-T", "host=x86", "-A", "win32"]

    print(args)
    subprocess.check_call(args, cwd=project_dir)

    # Build the project
    subprocess.check_call(
        [
            "cmake",
            "--build",
            "build",
            # "--config", "Release"
        ],
        cwd=project_dir,
    )


if __name__ == "__main__":
    cmake_build(use_vcpkg=os.environ.get("_USE_VCPKG", False))
