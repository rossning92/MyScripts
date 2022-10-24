set -e

if ! [ -x "$(command -v et)" ]; then
    sudo add-apt-repository ppa:jgmath2000/et -y
    sudo apt-get update
    sudo apt-get install et -y
fi

if ! [ -x "$(command -v expect)" ]; then
    sudo apt-get install expect -y
fi

cat >/tmp/et.sh <<EOF
set timeout 10
spawn et -x -r 5037:5037 -t 2222:22 {{ET_EXTRA_ARGS}} {{ET_USER}}@{{ET_HOST}}:{{ET_PORT}}
expect "password:"
send "{{ET_PWD}}\r"
{{ET_EXTRA_EXPECT_COMMANDS}}
interact
EOF

# mkdir ~/.screen || chmod 700 ~/.screen || true
# sudo /etc/init.d/screen-cleanup start

mkdir -p ~/.screen
chmod 700 ~/.screen # workaround for WSL
export SCREENDIR=$HOME/.screen

# Clean-up dead sessions
screen -wipe || true

out=$(screen -ls) || true
if [[ $out == *"screens on"* ]]; then
    echo "$out"
    read -p 'Please input session name: ' name
    screen -r $name # reattach
elif [[ $out == *"a screen on"* ]]; then
    screen -r # reattach
else
    screen -dmS et bash
    screen -r et -X stuff "expect /tmp/et.sh\n"
    screen -r et
fi

# screen -r et -X quit || true
