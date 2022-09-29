#!/bin/bash
set -e
cd "$(dirname "$0")/../../"
echo "Script dir: $(pwd)"

echo 'Confirm delete commit history? (y/n)'
read -n1 ans
if [ "$ans" == "y" ]; then
    git checkout --orphan tmp-branch
    git add -A
    git commit -m 'Initial commit'
    git branch -D master
    git branch -m master
    git branch --set-upstream-to=origin/master master
    git push --force
    git gc --aggressive --prune=all
fi
