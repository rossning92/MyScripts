# https://developer.android.com/ndk/guides/graphics/validation-layer#vl-external

set -e
pkg=${PKG_NAME}

if [[ -n "$VK_LAYER_NAME" ]]; then
    layername="$VK_LAYER_NAME"
else
    fullfile="$VK_LAYER_SO"
    filename="$(basename -- "$fullfile")"
    layername="VK_LAYER_${filename%.*}"
    layername="VK_LAYER_${layername#libVkLayer_}"
fi

echo "Push $VK_LAYER_SO to device..."
adb push "$VK_LAYER_SO" /data/local/tmp/$filename.so
adb shell run-as $pkg cp /data/local/tmp/$filename.so . #  same permission as the app
adb shell run-as $pkg ls $filename.so

echo "Enable gpu_debug_layers..."
adb shell settings put global enable_gpu_debug_layers 1
adb shell settings put global gpu_debug_app $pkg
adb shell settings put global gpu_debug_layers $layername
adb shell settings list global | grep gpu

run_script r/android/restart_app_logcat.py $pkg
