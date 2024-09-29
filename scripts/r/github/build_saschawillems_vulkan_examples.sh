run_script r/git/git_clone.sh https://github.com/SaschaWillems/Vulkan
cd ~/Projects/Vulkan

run_script ext/open_code_editor.py .

# https://github.com/SaschaWillems/Vulkan/blob/master/BUILD.md

run_script r/dev/cmake_build.py
