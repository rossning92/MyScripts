# Prerequisite:
# - BUILD_ANDROID_COMPILE_CPP
# - BUILD_ANDROID_INSTALL
# - UE_SOURCE
# - UE_PROJECT_DIR

run_script @cd=1 r/UE4/editor/build_ue4_editor.cmd
run_script @cd=1 r/UE4/uproject/build_cpp_modules.py
run_script @cd=1 r/UE4/uproject/build_android.py
run_script @cd=1 r/UE4/editor/run.py
