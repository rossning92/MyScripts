set -e
cd "$1"
du -h --max-depth=1 . | sort -rh | less -iS
