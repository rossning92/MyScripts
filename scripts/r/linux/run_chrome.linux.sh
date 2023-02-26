set -e
./install_google_chrome.sh
wmctrl -a '- Google Chrome' || google-chrome &
