set -e

cd '{{GIT_REPO}}'

curl -o .gitignore "https://raw.githubusercontent.com/github/gitignore/master/Unity.gitignore"

git init
git add -A
git commit -m "initial commit"
