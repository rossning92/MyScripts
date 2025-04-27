if git diff-index --quiet HEAD --; then
    git diff HEAD~1 HEAD | diff-so-fancy
else
    git diff | diff-so-fancy
fi
