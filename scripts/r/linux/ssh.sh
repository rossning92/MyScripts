if ! [ -x "$(command -v expect)" ]; then
    sudo apt-get install expect
fi

expect -c 'spawn ssh {{_USER}}@{{_HOST}}; expect "password:"; send "{{_PWD}}\r"; interact;'
