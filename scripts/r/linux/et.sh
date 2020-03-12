if ! [ -x "$(command -v et)" ]; then
    sudo add-apt-repository ppa:jgmath2000/et -y
    sudo apt-get update
    sudo apt-get install et -y
fi

# et -x -r 15037:5037 {{SSH_USER}}@{{SSH_HOST}}:8080
expect -c 'spawn et -x -r 15037:5037 -t 1234:22 {{SSH_USER}}@{{SSH_HOST}}:8080; expect "password:"; send "{{SSH_PWD}}\r"; interact;'
