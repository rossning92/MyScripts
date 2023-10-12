set -e
cd "$(mktemp -d)"
# run_script ext/open.py .
frida-trace -D {{ANDROID_SERIAL}} -i libvrapiimpl.so!vrapi_GetPredictedTracking2 {{PROC_NAME}}
