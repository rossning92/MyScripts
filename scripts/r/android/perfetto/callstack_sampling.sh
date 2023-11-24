# https://perfetto.dev/docs/quickstart/callstack-sampling
set -e
adb root

cd "$HOME"

# curl -LO https://raw.githubusercontent.com/google/perfetto/master/tools/cpu_profile
# chmod +x cpu_profile

python3 cpu_profile -n "surfaceflinger" -d 5000
