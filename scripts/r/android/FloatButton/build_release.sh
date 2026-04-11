#!/bin/bash
set -e
cd "$(dirname "$0")"

# Ensure ANDROID_HOME is set
if [ -z "$ANDROID_HOME" ]; then
    export ANDROID_HOME=~/Android/Sdk
fi

gradle assembleRelease

# Copy the built APK to the project root
cp app/build/outputs/apk/release/app-release.apk ./float-button-release.apk

echo "Release build finished."
ls -lh float-button-release.apk
