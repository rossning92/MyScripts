set -e
cd "$(mktemp -d)"

run_script r/android/frida/start_frida_android_server.sh

export PROC_NAME=$(run_script r/android/frida/list_all_proc.sh)
run_script ext/set_variable.py PROC_NAME $PROC_NAME

export MODULE_NAME=$(run_script r/android/frida/list_all_modules.sh)
run_script ext/set_variable.py MODULE_NAME $MODULE_NAME

FUNCTION_NAME=$(run_script r/android/frida/list_all_functions.sh)
run_script ext/set_variable.py FUNCTION_NAME $FUNCTION_NAME

find_js_file_and_open() {
    while true; do
        files=($(find . -type f -name "*.js"))
        if [ ${#files[@]} -gt 0 ]; then
            echo "Found JavaScript file: ${files[0]}"
            run_script ext/open_code_editor.py "${files[0]}"
            break
        fi
        sleep 1
    done
}

find_js_file_and_open &
frida-trace -D {{ANDROID_SERIAL}} -i $FUNCTION_NAME $PROC_NAME
