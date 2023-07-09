set -e

if [[ -n "$1" ]]; then
    pkg="$1"
else
    pkg="{{PKG_NAME}}"
fi

adb shell settings put global enable_gpu_debug_layers 1
adb shell settings put global gpu_debug_app $pkg
adb shell settings put global gpu_debug_layer_app org.renderdoc.renderdoccmd.arm64
adb shell settings put global gpu_debug_layers VK_LAYER_RENDERDOC_Capture
adb shell settings put global gpu_debug_layers_gles libVkLayer_GLES_RenderDoc.so

run_script r/android/restart_app.py $pkg
