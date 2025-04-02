set -e

# Install packages if not already installed
packages=("mingw-w64-x86_64-cmake" "mingw-w64-x86_64-ninja")
for package in "${packages[@]}"; do
    if ! pacman -Q $package >/dev/null 2>&1; then
        pacman -S $package --noconfirm
    fi
done

run_script r/git/git_clone.sh https://github.com/LunarG/VulkanTools
cd ~/Projects/VulkanTools

# https://github.com/LunarG/VulkanTools/blob/main/BUILD.md#android-build
cmake -S . -B build \
    -D CMAKE_TOOLCHAIN_FILE=$ANDROID_NDK_HOME/build/cmake/android.toolchain.cmake \
    -D ANDROID_PLATFORM=26 \
    -D CMAKE_ANDROID_ARCH_ABI=arm64-v8a \
    -D CMAKE_ANDROID_STL_TYPE=c++_static \
    -D ANDROID_USE_LEGACY_TOOLCHAIN_FILE=NO \
    -D CMAKE_BUILD_TYPE=Release \
    -D UPDATE_DEPS=ON \
    -G Ninja

cmake --build build

# python3 scripts/android.py --config Release --app-abi arm64-v8a
