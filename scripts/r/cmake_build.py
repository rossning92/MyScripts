import os

from _script import set_variable
from _shutil import call_echo, print2, shell_open

BUILD_LIB = "{{BUILD_LIB}}" == "Y"


if r"{{CMAKE_PROJECT_DIR}}":
    project_dir = r"{{CMAKE_PROJECT_DIR}}"
else:
    project_dir = os.environ["_CUR_DIR"]
    set_variable("CMAKE_PROJECT_DIR", project_dir)

print2("Project dir: %s" % project_dir)

project_name = os.path.basename(project_dir)

# Change to source folder
os.chdir(project_dir)

# Create CMakeList.txt
content = """cmake_minimum_required(VERSION 3.6)

project(%s)

# find_package(XXX)

include_directories(${PROJECT_SOURCE_DIR})

file(GLOB SRC_FILES
    "${PROJECT_SOURCE_DIR}/*.h"
    "${PROJECT_SOURCE_DIR}/*.cpp"
    "${PROJECT_SOURCE_DIR}/*.c"
)
%s(${CMAKE_PROJECT_NAME}
    ${SRC_FILES}
)

set(CMAKE_SUPPRESS_REGENERATION true)
set_property(DIRECTORY PROPERTY VS_STARTUP_PROJECT ${CMAKE_PROJECT_NAME})
set_target_properties(${CMAKE_PROJECT_NAME} PROPERTIES VS_DEBUGGER_WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}")
""" % (
    project_name,
    "add_library" if BUILD_LIB else "add_executable",
)

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

# call_echo(".\\build\\Release\\main.exe")

# shell_open("build\\thread.sln")
