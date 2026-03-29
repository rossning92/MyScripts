cd ~
args=("--repo-path" "chat_menu")
if [[ "$(uname -o)" == "Android" ]]; then
    args+=("--voice-input")
fi
run_script r/ai/coder.py "${args[@]}"
