set -e
name="$1"
commands="$2"

source "$(dirname "$0")/_wsl_screen_workaround.sh"

# Clean up dead screen sessions
screen -wipe >/dev/null 2>&1 || true

if ! screen -ls $name >/dev/null 2>&1; then
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
    if [[ -n "$commands" ]]; then
        screen -S $name -X stuff "$commands\n"
    fi
else
    echo "Screen \"$name\" already exists, skip."
fi
