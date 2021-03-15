if ! [ -x "$(command -v expect)" ]; then
    sudo apt-get update -y
    sudo apt-get install expect -y
fi

printf "Host *\nControlMaster auto\nControlPath ~/.ssh/master-%%r@%%h:%%p.socket\n" >~/.ssh/config

ssh -o "StrictHostKeyChecking no" {{_USER}}@{{_HOST}}

# sudo /etc/init.d/screen-cleanup start
# screen -r ssh_session -X quit
# screen -dmS ssh_session bash

# if [[ -z "{{_PWD}}" ]]; then
#     screen -r ssh_session -X stuff "ssh {{_USER}}@{{_HOST}}
# "
# else
#     screen -r ssh_session -X stuff "expect -c 'set timeout -1; spawn ssh -o \"StrictHostKeyChecking no\" -R 5037:localhost:5037 {{_USER}}@{{_HOST}}; expect \"password:\"; send \"{{_PWD}}\r\"; interact;'
# "
# fi

# screen -r ssh_session
