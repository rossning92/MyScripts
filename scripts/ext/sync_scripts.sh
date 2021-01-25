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

git status --short
status=$(git status --short)
if [[ ! -z "$status" ]]; then
    echo "Press ENTER to commit those files..."
    read -n 1 -s -r input
    
    if [[ -z $input ]]; then
        git add -A
        git commit -m 'commit with no message.'
    fi
fi

git pull --rebase
# git submodule update --recursive --remote
git push
