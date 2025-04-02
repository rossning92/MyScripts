set -e

cd 'C:\Users\rossning92\Projects\Vulkan-Tools\build-android\cmake\arm64-v8a\vulkaninfo'
adb push vulkaninfo /data/local/tmp/

adb shell chmod +x /data/local/tmp/vulkaninfo
adb shell /data/local/tmp/vulkaninfo
