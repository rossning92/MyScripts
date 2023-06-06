# https://developer.android.com/ndk/guides/graphics/validation-layer#vl-external

set -e
pkg=${PKG_NAME}

echo "Push ${VK_LAYER_SO} to device..."
adb push "${VK_LAYER_SO}" /data/local/tmp/libVkLayer_SAMPLE_SampleLayer.so
adb shell run-as ${pkg} cp /data/local/tmp/libVkLayer_SAMPLE_SampleLayer.so . #  same permission as the app
adb shell run-as ${pkg} ls libVkLayer_SAMPLE_SampleLayer.so

echo "Enable gpu_debug_layers..."
adb shell settings put global enable_gpu_debug_layers 1
adb shell settings put global gpu_debug_app ${pkg}
adb shell settings put global gpu_debug_layers VK_LAYER_SAMPLE_SampleLayer
adb shell settings put global gpu_debug_layers VK_LAYER_SAMPLE_SampleLayer
adb shell settings list global | grep gpu

run_script r/android/restart_app.py ${pkg}
