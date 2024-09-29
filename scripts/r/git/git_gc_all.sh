set -e
read -n1 -p 'This will expire all recent reflogs: (y/n)' ans
if [[ "$ans" == "y" ]]; then
    git reflog expire --expire=now --all
    git gc --prune=now --aggressive
fi
