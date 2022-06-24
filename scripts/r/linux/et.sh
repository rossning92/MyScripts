set -e

if ! [ -x "$(command -v et)" ]; then
    sudo add-apt-repository ppa:jgmath2000/et -y
    sudo apt-get update
    sudo apt-get install et -y
fi

if ! [ -x "$(command -v expect)" ]; then
    sudo apt-get install expect -y
fi

export SCREENDIR="$HOME/.screen"

# /usr/bin/expect <(
#     cat <<EOF
# EOF
# )

# expect "Passcode"; send "push\r"
cat >/tmp/et.sh <<EOF
set timeout 10
spawn et -x -r 5037:5037 -t 2222:22 {{ET_USER}}@{{ET_HOST}}:{{ET_PORT}}
expect "password:"
send "{{ET_PWD}}\r"
{{_EXTRA_EXPECT_COMMANDS}}
interact
EOF

# mkdir ~/.screen || chmod 700 ~/.screen || true
# sudo /etc/init.d/screen-cleanup start

mkdir -p ~/.screen
export SCREENDIR=$HOME/.screen

chmod 700 ~/.screen # workaround for WSL
screen -r ssh_session -X quit || true
screen -dmS ssh_session bash
screen -r ssh_session -X stuff "expect /tmp/et.sh\n"
screen -r ssh_session
