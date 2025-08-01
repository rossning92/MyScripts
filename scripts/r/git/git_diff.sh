if git diff-index --quiet HEAD --; then
    git diff --color HEAD~1 HEAD | less -R -+F
else
    git diff --color | less -R -+F
fi
