# https://developer.oculus.com/documentation/unity/ts-simpleperf/

set -e

if [[ -z "${ANDROID_NDK_HOME}" ]]; then
    echo 'Cannot find android ndk, please install first.'
    exit 1
fi

# cd 'C:\Android\android-sdk\ndk-bundle\simpleperf'
# cd "C:\Android\android-sdk\ndk\25.1.8937393\simpleperf"
# cd "C:\Android\android-sdk\ndk\21.4.7075529\simpleperf"
cd "${ANDROID_NDK_HOME}/simpleperf"

duration="${_DURATION}"
if [[ -z "$duration" ]]; then
    duration=5
fi

# python run_simpleperf_on_device.py stat -a --duration 1
# python run_simpleperf_on_device.py record -a -e cpu-clock --duration 3

args=''
if [[ -n "${_NATIVE_PROGRAM}" ]]; then
    args+="--native_program ${_NATIVE_PROGRAM}"
elif [[ -n "${_APP}" ]]; then
    args+="--app ${_APP}"
else
    args+="--app $(run_script r/android/get_active_package.py)"
fi

python3 app_profiler.py $args -r "-e task-clock:u -f 1000 -g --duration ${duration}"
python3 report_html.py

# adb pull /data/local/tmp/perf.data
# inferno.bat -sc --record_file perf.data
