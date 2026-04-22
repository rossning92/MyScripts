if git diff-index --quiet HEAD --; then
    git diff --color-moved --color-moved-ws=ignore-all-space HEAD~1 HEAD | less -R -+F
else
    git diff --color-moved --color-moved-ws=ignore-all-space | less -R -+F
fi
