set -e

# Clean-up dead sessions
screen -wipe || true

name="$1"
commands="$2"
if screen -ls $name; then
    echo "Reattach to screen session: $name"
    screen -r $name
else
    echo "Create new screen session: $name"
    # if [[ $(grep Microsoft /proc/version) ]]; then # WSL 1
    if false; then
        # HACK: If you run Windows commands within the current bash script, e.g.
        # cmd.exe, for some reason they will be killed when you close the
        # terminal. To avoid this, start a new session by running the `wsl`
        # command.
        wsl.exe -e bash -c "SCREENDIR=$HOME/.screen screen -dm -S $name bash"
        screen -S $name -X stuff "$commands\n"
    else
        screen -dm -S $name bash -c "$commands"
    fi
    screen -r $name
fi
