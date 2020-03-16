import os
from _shutil import *


def setup_cmake(version='3.10.2', install=False):
    if sys.platform == 'win32':
        if version:
            CMAKE_PATH = 'C:\\tools\\cmake-%s-win64-x64' % version
            if os.path.exists(CMAKE_PATH):
                prepend_to_path(CMAKE_PATH + os.path.sep + 'bin')
                return

            elif install:
                zip_file = os.path.realpath(expanduser(
                    '~/Downloads/cmake-%s-win64-x64.zip' % version))
                download('https://github.com/Kitware/CMake/releases/download/v3.10.2/cmake-3.10.2-win64-x64.zip',
                         filename=zip_file)
                unzip(zip_file, 'C:\\tools')
                prepend_to_path(CMAKE_PATH + os.path.sep + 'bin')
                return

        CMAKE_PATH = r'C:\Program Files\CMake\bin'
        if os.path.exists(CMAKE_PATH):
            print('CMake Path: %s' % CMAKE_PATH)
            prepend_to_path(CMAKE_PATH)
            return
