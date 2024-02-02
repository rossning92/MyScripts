set -e

if [[ -n "$BUILD_PROP_PATH" ]]; then
    build_prop_path="$BUILD_PROP_PATH"
else
    build_prop_path="/system/build.prop"
fi

adb root
adb remount

cd "$(mktemp -d)"
adb pull "$build_prop_path"

vim build.prop

adb push build.prop "$build_prop_path"
