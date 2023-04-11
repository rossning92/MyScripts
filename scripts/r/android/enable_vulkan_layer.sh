set -e

pkg=${PKG_NAME}
vkvalidationlayer="${VK_LAYER_SO}"

# https://developer.android.com/ndk/guides/graphics/validation-layer#vl-external

adb push "${vkvalidationlayer}" /data/local/tmp/libVkLayer_SAMPLE_SampleLayer.so
adb shell run-as ${pkg} cp /data/local/tmp/libVkLayer_SAMPLE_SampleLayer.so . #  same permission as the app
adb shell run-as ${pkg} ls libVkLayer_SAMPLE_SampleLayer.so

# enable layer
adb shell settings put global enable_gpu_debug_layers 1
adb shell settings put global gpu_debug_app ${pkg}
adb shell settings put global gpu_debug_layers VK_LAYER_SAMPLE_SampleLayer
adb shell settings put global gpu_debug_layers VK_LAYER_SAMPLE_SampleLayer
adb shell settings list global | grep gpu

# adb shell am force-stop ${pkg}
# adb shell monkey -p ${pkg} -c android.intent.category.LAUNCHER 1

run_script r/android/restart_app.py ${pkg}
