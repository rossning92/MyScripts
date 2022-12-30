if ! [ -x "$(command -v google-chrome)" ]; then
    cd /tmp/
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    sudo apt install ./google-chrome-stable_current_amd64.deb -y
    rm google-chrome-stable_current_amd64.deb
fi

wmctrl -a '- Google Chrome' || google-chrome
