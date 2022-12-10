#!/bin/bash
set -e
cd "$(dirname "$0")"

source install_expect.sh

# Config ControlMaster on the client side to share SSH connections (multiplexing)
mkdir -p ~/.ssh/
printf "Host *\nControlMaster auto\nControlPath ~/.ssh/master-%%r@%%h:%%p.socket\n" >~/.ssh/config

if [[ -z "${SSH_PORT}" ]]; then
    export SSH_PORT=22
fi

cat >/tmp/s.sh <<EOF
set timeout 10
spawn ssh -o "StrictHostKeyChecking no" ${SSH_USER}@${SSH_HOST} -p ${SSH_PORT} -R 5037:localhost:5037
expect "password:"
send "${SSH_PWD}\r"
${EXPECT_EXTRA_COMMANDS}
interact
EOF

./run_command_in_screen.sh "expect /tmp/s.sh"
