if [[ -x "$(command -v chromium)" ]]; then
    script_dir="$(dirname "${BASH_SOURCE[0]}")"
    policy_source="$script_dir/run_chrome.extensions-policy.json"
    policy_target="/etc/chromium/policies/managed/keepassxc-browser.json"
    browsercli_extension="$script_dir/../web/browsercli/extension"

    if ! cmp -s "$policy_source" "$policy_target"; then
        echo "Installing Chromium extension policy..."
        sudo install -D -o root -g root -m 0644 "$policy_source" "$policy_target"
    fi

    nohup chromium \
        --force-dark-mode \
        --disable-smooth-scrolling \
        --load-extension="$browsercli_extension" \
        >/dev/null 2>&1 &
fi
