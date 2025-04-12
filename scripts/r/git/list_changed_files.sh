if [ -z "$(git status --short)" ]; then
    git log -1 --pretty=oneline
    git diff --name-status HEAD~1 HEAD
else
    git status --short
fi
