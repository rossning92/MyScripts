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
    echo "Press (y) to continue..."
    read -n 1 -s -r input
    
    if [ "$input" = "y" ]; then
        git add -A
        git commit -m 'message'
        git pull --rebase
        git push
    fi
fi



