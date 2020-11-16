set -e

if ! [ -x "$(command -v et)" ]; then
    sudo add-apt-repository ppa:jgmath2000/et -y
    sudo apt-get update
    sudo apt-get install et -y
fi

if ! [ -x "$(command -v expect)" ]; then
    sudo apt-get install expect -y
fi

pkill screen || true
sudo /etc/init.d/screen-cleanup start

# screen -r ssh_session -X quit

screen -dmS ssh_session bash

# et -x -r 15037:5037 {{SSH_USER}}@{{SSH_HOST}}:8080

screen -r ssh_session -X stuff "expect -c 'set timeout -1; spawn et -x -r 5037:5037 -t 1234:22 {{SSH_USER}}@{{SSH_HOST}}:8080; expect \"password:\"; send \"{{SSH_PWD}}\r\"; interact;'
"

screen -r ssh_session
