# https://developer.android.com/ndk/guides/graphics/validation-layer#vl-external

set -e

pkg=${PKG_NAME}

if [[ -n "$VK_LAYER_NAME" ]]; then
    layername="$VK_LAYER_NAME"
else
    layername="VK_LAYER_${filename%.*}"
    layername="VK_LAYER_${layername#libVkLayer_}"
fi

filename="$(basename -- "$VK_LAYER_SO")"

echo "Push $VK_LAYER_SO to device..."
# adb push "$VK_LAYER_SO" /data/local/tmp/$filename
# adb shell run-as $pkg cp /data/local/tmp/$filename . #  same permission as the app
# adb shell run-as $pkg ls $filename
adb root
app_path=$(adb shell "pm path $pkg | sed -e 's/package://g' | sed -e 's/\/base\.apk//g'")
adb push "$VK_LAYER_SO" "${app_path}/lib/arm64/"

echo "Enable gpu_debug_layers..."
adb shell settings put global enable_gpu_debug_layers 1
adb shell settings put global gpu_debug_app $pkg
adb shell settings put global gpu_debug_layer_app $pkg
adb shell settings put global gpu_debug_layers $layername
adb shell setprop debug.vulkan.layers $layername # this will force enable layers globally
adb shell settings list global | grep gpu

start_script r/android/restart_app_logcat.sh $pkg
