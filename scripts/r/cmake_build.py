import sys
import os
import subprocess
import shutil

SRC_PATH = os.environ["CURRENT_FOLDER"]
BUILD_LIB = "{{BUILD_LIB}}" == "Y"

project_name = "example"
src_dir = SRC_PATH

if "SELECTED_FILE" in os.environ:
    f = os.environ["SELECTED_FILE"]
    if f.endswith(".cpp") or f.endswith(".c"):
        basename = os.path.basename(f)
        project_name = os.path.splitext(basename)[0]
        src_dir = os.path.dirname(f)

# Change to source folder
os.chdir(src_dir)

# Create CMakeList.txt
content = (
    """cmake_minimum_required(VERSION 2.7)

set(PROJECT_NAME """
    + project_name
    + """)

project(${PROJECT_NAME})
include_directories(${PROJECT_SOURCE_DIR})
set(SRC_FILES 
    ${PROJECT_SOURCE_DIR}/*.h
    ${PROJECT_SOURCE_DIR}/*.cpp
    ${PROJECT_SOURCE_DIR}/*.c
)
"""
    + ("add_library" if BUILD_LIB else "add_executable")
    + """(${PROJECT_NAME}
    ${SRC_FILES}
)

set(CMAKE_SUPPRESS_REGENERATION true)
set_property(DIRECTORY PROPERTY VS_STARTUP_PROJECT ${PROJECT_NAME})
set_target_properties(${PROJECT_NAME} PROPERTIES VS_DEBUGGER_WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}")
"""
)
if not os.path.exists("CMakeLists.txt"):
    with open("CMakeLists.txt", "w") as f:
        f.write(content)

# Add cmake to PATH
os.environ["PATH"] = r"C:\Program Files\CMake\bin" + os.pathsep + os.environ["PATH"]

# Create and switch to build folder
if not os.path.exists("build"):
    os.mkdir("build")
os.chdir("build")

# Remove cmake cache
if "{{CMAKE_REMOVE_CACHE}}" == "Y":
    if os.path.exists("CMakeCache.txt"):
        os.remove("CMakeCache.txt")

# Build
subprocess.call(["cmake", "-G" "Visual Studio 15 2017 Win64", ".."])
subprocess.call(["cmake", "--build", ".", "--config", "Release"])
