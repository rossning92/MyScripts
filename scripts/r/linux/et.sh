set -e

et_cmd="et --ssh-option \"Port {{SSH_PORT if SSH_PORT else 22}}\" --ssh-option \"StrictHostKeyChecking no\" {{ET_EXTRA_ARGS}} {{SSH_USER}}@{{SSH_HOST}}:{{ET_PORT if ET_PORT else 2022}}"

cat >~/et.sh <<EOF
set timeout 10
spawn ${et_cmd}

{{if SSH_PWD}}
expect "password:"
send "{{SSH_PWD}}\r"
{{end}}

{{ET_EXTRA_EXPECT_COMMANDS}}

interact
EOF

run_command_in_screen() {
    {{ include('r/linux/screen/run_command_in_screen.sh') }}
}
if [[ -n "{{_RUN_IN_SCREEN}}" ]]; then
    run_command_in_screen et "expect ~/et.sh"
else
    expect ~/et.sh
fi
