set -e

source "$(dirname "$0")/_wsl_screen_workaround.sh"

# Clean-up dead sessions
screen -wipe || true

name="$1"
commands="$2"
if screen -ls $name; then
    echo "Reattach to screen session: $name"
    screen -r $name
else
    echo "Create new screen session: $name"
    if [[ $(grep Microsoft /proc/version) ]]; then # WSL 1
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
