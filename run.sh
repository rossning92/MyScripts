#!/bin/bash

set -e

if [ "$(uname)" == "Linux" ]; then
    if ! type pip3 >/dev/null; then
        sudo apt install python3-pip -y
    fi
fi

pip3 install -r requirement.txt
python3 main_console.py
