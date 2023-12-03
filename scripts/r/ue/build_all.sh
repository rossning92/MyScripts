# Prerequisite:
# - BUILD_ANDROID_COMPILE_CPP
# - BUILD_ANDROID_INSTALL
# - UE_SOURCE
# - UE_PROJECT_DIR
# - UE_ANDROID_OUT_DIR

run_script @cd=1 r/ue/editor/build_ue4_editor.cmd
run_script @cd=1 r/ue/uproject/build_cpp_modules.py
run_script @cd=1 r/ue/uproject/build_android.py
run_script @cd=1 r/ue/editor/run.py
