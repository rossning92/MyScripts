set -e

cmd /c ndk-build

adb root
adb shell setenforce 0
adb shell mkdir -p /data/local/debug/gles
adb push libs/arm64-v8a/libGLES_glesLayer.so /data/local/debug/gles/

# Enable layer
adb shell settings put global enable_gpu_debug_layers 1
adb shell settings put global gpu_debug_app $PKG_NAME
adb shell settings put global gpu_debug_layers_gles libGLES_glesLayer.so

run_script r/android/restart_app_logcat.py $PKG_NAME
