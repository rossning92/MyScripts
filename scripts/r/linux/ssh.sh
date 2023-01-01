#!/bin/bash
set -e
cd "$(dirname "$0")"

run_script ext/install_pkg.py expect

# Config ControlMaster on the client side to share SSH connections (multiplexing)
# mkdir -p ~/.ssh/
# printf "Host *\nControlMaster auto\nControlPath ~/.ssh/master-%%r@%%h:%%p.socket\n" >~/.ssh/config

# Port
if [[ -z "${SSH_PORT}" ]]; then
    export SSH_PORT=22
fi

# -t: interactive
ssh_command="ssh -t ${SSH_USER}@${SSH_HOST} -o \"StrictHostKeyChecking no\" -p ${SSH_PORT}"
if [ -n "${SSH_LOCAL_PORT_FORWARD}" ]; then
    ssh_command+=" -L ${SSH_LOCAL_PORT_FORWARD}:localhost:${SSH_LOCAL_PORT_FORWARD}"
fi

if [ -n "${SSH_EXEC_COMMANDS}" ]; then
    ssh_command+=" ${SSH_EXEC_COMMANDS}"
fi

# SSH login automation
cat >~/s.expect <<EOF
set timeout 10
spawn ${ssh_command}
expect "password:"
send "${SSH_PWD}\r"
${EXPECT_EXTRA_COMMANDS}
interact
EOF

if [ -n "${RUN_IN_SCREEN}" ]; then
    ./run_command_in_screen.sh "expect ~/s.expect"
else
    expect ~/s.expect
fi
