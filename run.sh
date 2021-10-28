#!/bin/bash
cd "$(dirname "$0")"

set -e

if [ "$(uname)" == "Linux" ]; then
    if ! type pip3 >/dev/null; then
        sudo apt-get update
        sudo apt install python3-pip -y
    fi
fi

pip3 install -r requirement.txt
python3 main_console.py
