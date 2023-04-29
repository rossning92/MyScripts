set -e

run_script r/linux/install_et.sh
run_script ext/install_pkg.py expect

if [[ -n "${ET_PORT}" ]]; then
    port="${ET_PORT}"
else
    port=2022
fi

cmdline="et -x ${ET_EXTRA_ARGS} ${SSH_USER}@${SSH_HOST}:${port}"
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
    "$(dirname "$0")/run_command_in_screen.sh" et "expect ~/et.sh"
else
    expect ~/et.sh
fi
