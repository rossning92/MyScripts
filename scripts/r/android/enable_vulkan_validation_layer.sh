set -e

pkg=${PKG_NAME}
vkvalidationlayer="${VK_VALIDATION_LAYER_SO}"

# https://developer.android.com/ndk/guides/graphics/validation-layer#vl-external

adb push "${vkvalidationlayer}" /data/local/tmp/libVkLayer_khronos_validation.so
adb shell run-as ${pkg} cp /data/local/tmp/libVkLayer_khronos_validation.so . #  same permission as the app
adb shell run-as ${pkg} ls libVkLayer_khronos_validation.so

# enable layer
adb shell settings put global enable_gpu_debug_layers 1
adb shell settings put global gpu_debug_app ${pkg}
adb shell settings put global gpu_debug_layers VK_LAYER_KHRONOS_validation
adb shell settings put global gpu_debug_layers VK_LAYER_KHRONOS_validation
adb shell settings list global | grep gpu

adb shell am force-stop ${pkg}
adb shell monkey -p ${pkg} -c android.intent.category.LAUNCHER 1
adb logcat | grep 'VALIDATION'
