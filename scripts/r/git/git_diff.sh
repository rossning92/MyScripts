if git diff-index --quiet HEAD --; then
    git diff HEAD~1 HEAD
else
    git diff
fi
