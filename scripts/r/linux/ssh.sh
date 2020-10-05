if ! [ -x "$(command -v expect)" ]; then
    sudo apt-get update -y
    sudo apt-get install expect -y
fi

printf "Host *\nControlMaster auto\nControlPath ~/.ssh/master-%%r@%%h:%%p.socket\n" >~/.ssh/config

if [[ -z "{{_PWD}}" ]]; then
    ssh {{_USER}}@{{_HOST}}
else
    expect -c 'set timeout -1; spawn ssh -o "StrictHostKeyChecking no" -R 5037:localhost:5037 {{_USER}}@{{_HOST}}; expect "password:"; send "{{_PWD}}\r"; interact;'
fi
