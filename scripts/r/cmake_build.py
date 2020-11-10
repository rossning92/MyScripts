import sys
import os
import subprocess
import shutil
from _shutil import *


BUILD_LIB = "{{BUILD_LIB}}" == "Y"

project_name = "example"

if r"{{_PROJ_DIR}}":
    project_dir = r"{{_PROJ_DIR}}"
else:
    project_dir = os.environ["CUR_DIR_"]

print2("Project dir: %s" % project_dir)


# if "_FILE" in os.environ:
#     f = os.environ["_FILE"]
#     if f.endswith(".cpp") or f.endswith(".c"):
#         basename = os.path.basename(f)
#         project_name = os.path.splitext(basename)[0]
#         project_dir = os.path.dirname(f)

# Change to source folder
os.chdir(project_dir)

# Create CMakeList.txt
content = (
    """cmake_minimum_required(VERSION 2.7)

project("""
    + project_name
    + """)

# find_package(XXX)

include_directories(${PROJECT_SOURCE_DIR})

file(GLOB SRC_FILES
    "${PROJECT_SOURCE_DIR}/*.h"
    "${PROJECT_SOURCE_DIR}/*.cpp"
    "${PROJECT_SOURCE_DIR}/*.c"
)
"""
    + ("add_library" if BUILD_LIB else "add_executable")
    + """(main
    ${SRC_FILES}
)
"""
)

# XXX: Removed from CMakeLists.txt
# set(CMAKE_SUPPRESS_REGENERATION true)
# set_property(DIRECTORY PROPERTY VS_STARTUP_PROJECT main)
# set_target_properties(main PROPERTIES VS_DEBUGGER_WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}")

if not os.path.exists("CMakeLists.txt"):
    with open("CMakeLists.txt", "w") as f:
        f.write(content)

# Add cmake to PATH
os.environ["PATH"] = r"C:\Program Files\CMake\bin" + os.pathsep + os.environ["PATH"]

# shutil.rmtree("build")

# Remove cmake cache
if "{{CMAKE_REMOVE_CACHE}}" == "Y":
    if os.path.exists("CMakeCache.txt"):
        os.remove("CMakeCache.txt")

# Build
args = []
# args = ["cmake", "-G" "Visual Studio 15 2017 Win64", ".."]
args += [
    "cmake",
    "-DCMAKE_TOOLCHAIN_FILE=C:/Users/Ross/vcpkg/scripts/buildsystems/vcpkg.cmake",
    "-B",
    "build",
    "-S",
    ".",
]
call_echo(args)
call_echo(["cmake", "--build", "build", "--config", "Release"])

call_echo(".\\build\\Release\\main.exe")

# os.chdir("Release")
# print("Run executable: %s" % project_name)
# subprocess.call(project_name, shell=True)
