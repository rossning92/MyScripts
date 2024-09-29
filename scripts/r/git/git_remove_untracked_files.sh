set -e
git clean -n -x -d
read -n1 -p 'This will remove all untracked files, continue? (y/n)' ans
if [[ "$ans" == 'y' ]]; then
    git clean -f -x -d
fi
