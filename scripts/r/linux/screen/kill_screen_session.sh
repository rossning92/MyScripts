set -e

name="$1"

# Kill screen sessions by name
screen -ls | grep $name | cut -d. -f1 | awk '{print $1}' | xargs kill
