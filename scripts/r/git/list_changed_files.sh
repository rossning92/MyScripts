if [ -z "$(git status --short)" ]; then
    git log -1 --pretty=oneline
    git diff --name-status HEAD HEAD~1
else
    git status --short
fi
