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
[[ -z "$status" ]] && exit 0

echo "Press y to commit..."
read -n1 ans
[[ "$ans" != "y" ]] && exit 0

git add -A
git commit -m 'commit with no message.'

git pull --rebase
# git submodule update --recursive --remote
git push
