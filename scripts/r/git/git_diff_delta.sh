if git diff-index --quiet HEAD --; then
    git diff --color HEAD~1 HEAD | delta --side-by-side
else
    git diff --color | delta --side-by-side
fi
