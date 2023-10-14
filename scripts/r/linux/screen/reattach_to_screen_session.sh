set -e
name="$1"
echo "Reattach to screen session: $name"
# -x resumes a not-detached screen
screen -x $name
