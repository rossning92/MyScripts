if ! [ -x "$(command -v expect)" ]; then
    sudo apt update
    sudo apt install expect -y
fi
