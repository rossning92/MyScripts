set -e
adb root

adb uninstall org.renderdoc.renderdoccmd.arm32 || true
adb uninstall org.renderdoc.renderdoccmd.arm64 || true

adb shell settings delete global enable_gpu_debug_layers
adb shell settings delete global gpu_debug_app
adb shell settings delete global gpu_debug_layer_app
adb shell settings delete global gpu_debug_layers
adb shell settings delete global gpu_debug_layers_gles
