# https://github.com/baldurk/renderdoc/blob/v1.x/docs/CONTRIBUTING/Compiling.md

set -e

cd "C:\Users\rossning92\Projects\renderdoc"

# pacman -S mingw-w64-x86_64-cmake
# pacman -S mingw-w64-x86_64-make
# pacman -S mingw-w64-x86_64-gcc

export JAVA_HOME="C:\Program Files\Java\jdk1.8.0_211"
export PATH="C:\Program Files\Java\jdk1.8.0_211\bin:${PATH}"

# Build Android
(
    # arm32
    mkdir -p build-android
    cd build-android
    cmake -DBUILD_ANDROID=On -DANDROID_ABI=armeabi-v7a -G "MinGW Makefiles" ..
    mingw32-make
)
(
    # arm64
    mkdir -p build-android64
    cd build-android64
    cmake -DBUILD_ANDROID=On -DANDROID_ABI=arm64-v8a -G "MinGW Makefiles" ..
    mingw32-make
)

mkdir -p plugins/android/
cp build-android/bin/org.renderdoc.renderdoccmd.arm32.apk x64/Development/plugins/android/
cp build-android64/bin/org.renderdoc.renderdoccmd.arm64.apk x64/Development/plugins/android/
