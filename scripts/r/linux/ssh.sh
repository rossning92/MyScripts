if ! [ -x "$(command -v expect)" ]; then
    sudo apt-get install expect
fi

if [[ -z "{{_PWD}}" ]]; then
    ssh {{_USER}}@{{_HOST}}
else
    expect -c 'spawn ssh {{_USER}}@{{_HOST}}; expect "password:"; send "{{_PWD}}\r"; interact;'
fi
