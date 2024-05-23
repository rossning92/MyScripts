import glob
import logging
import os
import subprocess
import sys
import tempfile

from _shutil import download, prepend_to_path, unzip


def find_cmake_path(cmake_version):
    found = glob.glob("C:\\tools\\cmake-%s*" % cmake_version)
    if found:
        return found[0]
    else:
        return None


def setup_cmake(cmake_version=None, install=True, env=None):
    if sys.platform == "win32":
        if cmake_version:
            cmake_path = find_cmake_path(cmake_version=cmake_version)
            if cmake_path:
                prepend_to_path(os.path.join(cmake_path, "bin"), env=env)
                return True

            elif install:
                zip_file = os.path.join(
                    tempfile.gettempdir(), "cmake-%s-win64-x64.zip" % cmake_version
                )

                download(
                    "https://github.com/Kitware/CMake/releases/download/v%s/cmake-%s-win64-x64.zip"
                    % (cmake_version, cmake_version),
                    filename=zip_file,
                )
                unzip(zip_file, "C:\\tools")
                cmake_path = find_cmake_path(cmake_version=cmake_version)
                assert cmake_path is not None
                prepend_to_path(os.path.join(cmake_path, "bin"), env=env)
                return True

        def find_cmake(cmake_path):
            match = glob.glob(cmake_path)
            if match:
                cmake_path = sorted(match)[-1]
                logging.info("CMake: install path: %s" % cmake_path)
                prepend_to_path(os.path.join(cmake_path, "bin"), env=env)
                return True

        if find_cmake(r"C:\Program Files\CMake"):
            return True

        if find_cmake(r"C:\tools\cmake-*"):
            return True

        return False


def compile(file):
    args = []

    if file.endswith(".cpp") or file.endswith(".cc"):
        args += ["clang++"]
    elif file.endswith(".c"):
        args += ["clang"]
    else:
        raise Exception("Invalid source file: %s" % file)

    # Specify output file
    out_file = os.path.splitext(file)[0] + (".exe" if sys.platform == "win32" else "")

    # Compile if source file is newer than the executable
    args += [
        "-O2",
        "-pipe",
        "-o",
        out_file,
    ]

    # Specify source file
    args += [file]

    subprocess.check_call(args)

    return out_file
