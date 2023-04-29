set -e
run_script ext/install_pkg.py screen

# mkdir ~/.screen || chmod 700 ~/.screen || true
# sudo /etc/init.d/screen-cleanup start

# HACK: for WSL
if [[ $(grep Microsoft /proc/version) ]]; then
    mkdir -p ~/.screen
    chmod 700 ~/.screen
    export SCREENDIR=$HOME/.screen
fi

# Clean-up dead sessions
screen -wipe || true

name="$1"
commands="$2"
if screen -ls $name; then
    echo "Reattach to screen session: $name"
    screen -r $name
else
    echo "Create a new screen session: $name"
    if [[ $(grep Microsoft /proc/version) ]]; then
        # HACK: If you run Windows commands within the current bash script, e.g.
        # cmd.exe, for some reason they will be killed when you close the
        # terminal. To avoid this, start a new session by running the `wsl`
        # command.
        wsl.exe -e bash -c "SCREENDIR=$HOME/.screen screen -dm -S $name bash"
    else
        screen -dm -S $name bash
    fi
    screen -S $name -X stuff "$commands\n"
    screen -r $name
fi

# out=$(screen -ls) || true
# if [[ $out == *"screens on"* ]]; then
#     echo "$out"
#     read -p 'Please input session name: ' name
#     screen -d -r $name # reattach
# elif [[ $out == *"a screen on"* ]]; then
#     screen -d -r # reattach
# else
#     screen -mS et bash -c "$1"

#     # screen -dmS et bash  # create screen named "et" and run "bash"
#     # screen -r et -X stuff "$1\n"  # send stuff
#     # screen -r et  # reattach
# fi

# screen -r et -X quit || true
