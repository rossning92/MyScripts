cmake_minimum_required(VERSION 3.12)

set(PROJECT_NAME example)

project(${PROJECT_NAME})

file(GLOB srcs "*.h" "*.cpp")
add_executable(${PROJECT_NAME} ${srcs})

set(CMAKE_SUPPRESS_REGENERATION true)
set_property(DIRECTORY PROPERTY VS_STARTUP_PROJECT ${PROJECT_NAME})
set_target_properties(${PROJECT_NAME} PROPERTIES VS_DEBUGGER_WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}")
