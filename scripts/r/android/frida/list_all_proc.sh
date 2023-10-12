frida-ps --device {{ANDROID_SERIAL}} | fzf | awk '{print $2}' | clip
