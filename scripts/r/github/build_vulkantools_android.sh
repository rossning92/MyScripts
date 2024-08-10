set -e

# https://github.com/LunarG/VulkanTools/blob/main/BUILD.md#android-build

which cmake
which ninja

export CMAKE_GENERATOR=Ninja

run_script r/git/git_clone.sh https://github.com/LunarG/VulkanTools
cd ~/Projects/VulkanTools

cmake -S . -B build \
    -D CMAKE_TOOLCHAIN_FILE=$ANDROID_NDK_HOME/build/cmake/android.toolchain.cmake \
    -D ANDROID_PLATFORM=26 \
    -D CMAKE_ANDROID_ARCH_ABI=arm64-v8a \
    -D CMAKE_ANDROID_STL_TYPE=c++_static \
    -D ANDROID_USE_LEGACY_TOOLCHAIN_FILE=NO \
    -D CMAKE_BUILD_TYPE=Release \
    -D UPDATE_DEPS=ON \
    -D CMAKE_MAKE_PROGRAM="C:\ProgramData\chocolatey\bin\ninja.exe" \
    -G Ninja

cmake --build build
