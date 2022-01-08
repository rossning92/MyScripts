import os
import sys
import tempfile

from _shutil import download, prepend_to_path, unzip
import glob


def find_cmake_path(cmake_version):
    found = glob.glob("C:\\tools\\cmake-%s*" % cmake_version)
    if found:
        return found[0]
    else:
        return None


def setup_cmake(cmake_version="3.21.1", install=True):
    if sys.platform == "win32":
        if cmake_version:
            cmake_path = find_cmake_path(cmake_version=cmake_version)
            if cmake_path:
                prepend_to_path(cmake_path + os.path.sep + "bin")
                return

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
                prepend_to_path(cmake_path + os.path.sep + "bin")
                return

        cmake_path = r"C:\Program Files\CMake\bin"
        if os.path.exists(cmake_path):
            print("CMake Path: %s" % cmake_path)
            prepend_to_path(cmake_path)
            return
