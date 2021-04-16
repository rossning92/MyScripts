set -e

cd ../..

git config --global user.email "rossning92@github.com"
git config --global user.name "rossning92"
git config credential.helper store

if [ ! -d ".git" ]; then
    git init
    git remote add origin https://github.com/rossning92/MyScripts
    git fetch
    git reset --hard origin/master
    git branch --set-upstream-to=origin/master master
fi

# Check if file is modified
git status --short
status=$(git status --short)
if [[ ! -z "$status" ]]; then
    echo "Press y to commit..."
    read -n1 ans
    if [[ "$ans" == "y" ]]; then
        git add -A
        git commit -m 'commit with no message.'
    else
        exit 0
    fi
fi

git pull --rebase
# git submodule update --recursive --remote
git push
