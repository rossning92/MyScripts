#!/bin/bash
set -e
cd "$(dirname "$0")/../../"
echo "Script dir: $(pwd)"

if [ ! -d ".git" ]; then
    git init
    git remote add origin https://github.com/rossning92/MyScripts
    git fetch
    git reset --hard origin/master
    git branch --set-upstream-to=origin/master master
fi

git config --global user.email "rossning92@gmail.com"
git config --global user.name "Ross Ning"
git config credential.helper store

# Check if file is modified
git status --short
status=$(git status --short)
if [[ ! -z "$status" ]]; then
    if [[ -n "$AMEND" ]]; then
        echo "Press y to amend (DANGEROUS!)"
    else
        echo "Press y to commit..."
    fi
    read -n1 ans
    if [[ "$ans" == "y" ]]; then
        git add -A
        git restore --staged scripts/r/videoedit/movy
        if [[ -n "$AMEND" ]]; then
            git commit --amend --no-edit
        else
            git commit -m 'commit with no message.'
        fi
    else
        exit 0
    fi
fi

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
