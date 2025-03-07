# https://perfetto.dev/docs/contributing/build-instructions#standalone-builds

set -e -x

{{ include('_setup_perfetto_project.sh') }}

tools/install-build-deps --android

mkdir -p out/
mkdir -p out/android
cat >out/android/args.gn <<EOF
target_os = "android"
target_cpu = "arm64"

is_debug = true
cc_wrapper = "ccache"
EOF
tools/gn gen out/android

tools/ninja -C out/android

# Kill existing processes in case they are already running.
adb shell killall traced || true
adb shell killall traced_probes || true

{{ include('r/android/adb_remount.sh') }}
adb push out/android/perfetto /system/bin/
adb push out/android/traced /system/bin/
adb push out/android/libperfetto.so /system/lib64/
