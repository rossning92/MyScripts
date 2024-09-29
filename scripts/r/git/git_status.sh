if [ -z "$(git status --porcelain)" ]; then
    echo 'Working tree is clean. Changed files in HEAD:'
    git diff-tree --no-commit-id --name-only -r HEAD
else
    echo 'Changed files in working tree:'
    git status --short
fi

{{ include('r/git/git_log.sh') }}
