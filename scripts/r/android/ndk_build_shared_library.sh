#!/bin/bash

# Check if an argument is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <file>"
    exit 1
fi

# Get the directory containing the file
dir=$(dirname "$1")

target=$(basename "$1" .${1##*.})
src_file=$(basename "$1")

mkdir -p jni

# Define the Android.mk file content
cat >jni/Android.mk <<EOF
LOCAL_PATH := \$(call my-dir)

include \$(CLEAR_VARS)

LOCAL_MODULE     := $target
LOCAL_SRC_FILES  := ../$src_file
LOCAL_CPPFLAGS   += -std=c++11

include \$(BUILD_SHARED_LIBRARY)
EOF

# Define the Application.mk file content
cat >jni/Application.mk <<EOF
APP_STL := c++_shared
APP_ABI := armeabi-v7a arm64-v8a
EOF

# Build the project using ndk-build
cmd /c ndk-build
