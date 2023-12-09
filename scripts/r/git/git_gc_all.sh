set -e

if [[ -n "$GIT_REPO" ]]; then
    cd "$GIT_REPO"
fi

git reflog expire --expire=now --all
git gc --prune=now --aggressive
