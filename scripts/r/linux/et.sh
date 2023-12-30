set -e

et_port="${ET_PORT:-2022}"
ssh_port="${SSH_PORT:-22}"

cmdline="et -x --ssh-option \"Port $ssh_port\" ${ET_EXTRA_ARGS} ${SSH_USER}@${SSH_HOST}:${et_port}"
echo "${cmdline}"

cat >~/et.sh <<EOF
set timeout 10
spawn ${cmdline}
expect "password:"
send "${SSH_PWD}\r"
${ET_EXTRA_EXPECT_COMMANDS}
interact
EOF

if [[ -n "${_RUN_IN_SCREEN}" ]]; then
    "$(dirname "$0")/screen/run_command_in_screen.sh" et "expect ~/et.sh"
else
    expect ~/et.sh
fi
