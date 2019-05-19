cd ../..

git config credential.helper store

if [ ! -d ".git" ]; then
	git init
	git remote add origin https://github.com/rossning92/MyScripts
	git fetch
	git reset --hard origin/master
	git branch --set-upstream-to=origin/master master
fi

status=$(git status --short)
echo $status
if [[ ! -z "$status" ]]; then
    read -n 1 -s -r -p "Press (y) to continue..."
    git add -A
    git commit -m 'message'
    git pull --rebase
    git push
fi



