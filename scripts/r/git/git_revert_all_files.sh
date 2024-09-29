git status --short
read -n1 -p 'This will revert all files, continue? (y/n)' ans
if [[ "$ans" == 'y' ]]; then
    git reset HEAD --hard
fi
