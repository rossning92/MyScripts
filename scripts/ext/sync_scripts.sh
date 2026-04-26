#!/bin/bash
set -e
cd "$(dirname "$0")/../../"
if [[ -n "$AMEND" ]]; then
    echo "Sync repo (amend): $(pwd)"
else
    echo "Sync repo: $(pwd)"
fi

# Check if file is modified
git status --short
status=$(git status --short)
if [[ ! -z "$status" ]]; then
    echo "Confirm? (y/n)"
    read -n1 ans
    if [[ "$ans" == "y" ]]; then
        git add -A

        if [[ -n "$AMEND" ]]; then
            git commit --amend --no-edit
        else
            git commit -m 'No commit message'
        fi
    else
        exit 0
    fi
fi

echo 'Sync changes with remote...'
if [[ -n "$AMEND" ]]; then
    git push --force
else
    git pull --rebase

    # Update submodules
    # git pull --recurse-submodules || true
    if (cd scripts/r/videoedit/movy && git diff --quiet); then
        echo "Update submodule movy..."
        git submodule update --recursive --remote || true
    else
        echo "(Skip updating submodule movy - working tree is dirty.)"
    fi

    git push
fi
