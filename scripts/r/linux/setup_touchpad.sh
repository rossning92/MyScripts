set -e
touchpad="$(xinput list --name-only | grep -i touch)"
echo "Setup touchpad device: $touchpad"
xinput set-prop "$touchpad" "libinput Tapping Enabled" 1
xinput set-prop "$touchpad" "libinput Natural Scrolling Enabled" 1
