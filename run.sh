#!/bin/bash
cd "$(dirname "$0")"

set -e

if [ "$(uname)" == "Linux" ]; then
    if ! type pip3 >/dev/null; then
        sudo apt-get update
        sudo apt install python3-pip -y
    fi

    if ! [ -x "$(command -v sxhkd)" ]; then
        sudo apt-get update
        sudo apt-get install sxhkd -y
    fi

    if ! [ -x "$(command -v kitty)" ]; then
        sudo apt-get update
        sudo apt-get install kitty -y
    fi

    if ! [ -x "$(command -v xdotool)" ]; then
        sudo apt-get update
        sudo apt-get install xdotool -y
    fi
fi

pip3 install -r requirement.txt
python3 main_console.py
