set -e
source "$(dirname "$0")/_wsl_screen_workaround.sh"
name="$1"
echo "Reattach to screen session: $name"
# -x resumes a not-detached screen
screen -x $name
