set -e

cd '{{GIT_REPO}}'

curl -o .gitignore "https://raw.githubusercontent.com/github/gitignore/master/UnrealEngine.gitignore"

git init
git add -A
git commit -m "initial commit"

start_script r/git/git_tools.py
