set -e
set -x
run_script r/git/git_clone.sh https://github.com/KhronosGroup/Vulkan-Tools
cd ~/Projects/Vulkan-Tools

# Build release binaries for arm64-v8a
python3 scripts/android.py --config Release --app-abi arm64-v8a --app-stl c++_static
