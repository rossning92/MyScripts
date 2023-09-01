"$(dirname "$0")/install_google_chrome.sh"

if [[ -x "$(command -v google-chrome)" ]]; then
    nohup google-chrome >/dev/null 2>&1 &
elif [[ -x "$(command -v google-chrome-stable)" ]]; then
    nohup google-chrome-stable >/dev/null 2>&1 &
fi
