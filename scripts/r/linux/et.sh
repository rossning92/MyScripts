set -e

et_cmd="et -x --ssh-option \"Port {{SSH_PORT if SSH_PORT else 22}}\" {{ET_EXTRA_ARGS}} {{SSH_USER}}@{{SSH_HOST}}:{{ET_PORT if ET_PORT else 2022}}"
echo "${et_cmd}"

cat >~/et.sh <<EOF
set timeout 10
spawn ${et_cmd}
expect "password:"
send "{{SSH_PWD}}\r"
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
