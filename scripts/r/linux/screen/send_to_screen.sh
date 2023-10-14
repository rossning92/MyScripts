set -e

name="$1"
command="$2"
screen -S $name -X stuff "${command}"
