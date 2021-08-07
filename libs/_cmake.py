import os
import sys
import tempfile

from _shutil import download, prepend_to_path, unzip


def setup_cmake(version="3.21.1", install=True):
    if sys.platform == "win32":
        if version:
            CMAKE_PATH = "C:\\tools\\cmake-%s-windows-x86_64" % version
            if os.path.exists(CMAKE_PATH):
                prepend_to_path(CMAKE_PATH + os.path.sep + "bin")
                return

            elif install:
                zip_file = os.path.join(
                    tempfile.gettempdir(), "cmake-%s-win64-x64.zip" % version
                )

                download(
                    "https://github.com/Kitware/CMake/releases/download/v%s/cmake-%s-windows-x86_64.zip"
                    % (version, version),
                    filename=zip_file,
                )
                unzip(zip_file, "C:\\tools")
                assert os.path.exists(CMAKE_PATH)
                prepend_to_path(CMAKE_PATH + os.path.sep + "bin")
                return

        CMAKE_PATH = r"C:\Program Files\CMake\bin"
        if os.path.exists(CMAKE_PATH):
            print("CMake Path: %s" % CMAKE_PATH)
            prepend_to_path(CMAKE_PATH)
            return
