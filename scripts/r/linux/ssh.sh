# if ! [ -x "$(command -v expect)" ]; then
#     sudo apt-get update -y
#     sudo apt-get install expect -y
# fi

# Config ControlMaster on the client side to share SSH connections (multiplexing)
printf "Host *\nControlMaster auto\nControlPath ~/.ssh/master-%%r@%%h:%%p.socket\n" >~/.ssh/config

s=$(
    cat <<'EOF'
set timeout 10

spawn ssh -o "StrictHostKeyChecking no" {{_USER}}@{{_HOST}} -R 5037:localhost:5037
expect "password:"
send "{{SSH_PWD}}\r"
expect "Passcode or option"
send "push\r"
interact
EOF
)
expect -c "$s"
