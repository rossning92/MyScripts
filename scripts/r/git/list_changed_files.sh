if [ -z "$(git status --short)" ]; then
    echo "(working directory clean, changed files in HEAD:)"
    git diff-tree --no-commit-id --name-only -r HEAD
else
    git status --short
fi
