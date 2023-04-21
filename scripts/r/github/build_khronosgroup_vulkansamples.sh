# https://github.com/KhronosGroup/Vulkan-Samples#setup
# https://github.com/KhronosGroup/Vulkan-Samples/blob/main/docs/build.md#android

set -e

run_script r/git/git_clone.sh "https://github.com/KhronosGroup/Vulkan-Samples"
cd ~/Projects/Vulkan-Samples

bldsys/scripts/generate_android_gradle.bat

adb push --sync assets /sdcard/Android/data/com.khronos.vulkan_samples/files/
adb push --sync shaders /sdcard/Android/data/com.khronos.vulkan_samples/files/

cd build/android_gradle

gradle installDebug
# gradle installDebug --info

# Workaround: for Android 11+
adb shell pm grant com.khronos.vulkan_samples android.permission.READ_EXTERNAL_STORAGE
adb shell pm grant com.khronos.vulkan_samples android.permission.WRITE_EXTERNAL_STORAGE
