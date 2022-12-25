set -e

source install_et.sh
source install_expect.sh

if [[ -n "{{ET_PORT}}" ]]; then
    port="{{ET_PORT}}"
else
    port=2022
fi

cat >/tmp/s.sh <<EOF
set timeout 10
spawn et -x -r 5037:5037 -t 2222:22 {{ET_EXTRA_ARGS}} {{SSH_USER}}@{{SSH_HOST}}:${port}
expect "password:"
send "{{SSH_PWD}}\r"
{{ET_EXTRA_EXPECT_COMMANDS}}
interact
EOF

./run_command_in_screen.sh "expect /tmp/s.sh"
