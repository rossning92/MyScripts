import os


def setup_cmake():
    cmake_bin = r'C:\Program Files\CMake\bin'
    if os.path.exists(cmake_bin):
        print('CMake Path: %s' % cmake_bin)
        os.environ['PATH'] = cmake_bin + os.pathsep + os.environ['PATH']
