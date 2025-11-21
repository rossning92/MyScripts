#!/bin/bash
git_diff="git diff --color --ignore-space-change --color-moved=dimmed-zebra --color-moved-ws=allow-indentation-change"
git diff-index --quiet HEAD -- && git_diff+=" HEAD~1 HEAD"
$git_diff | diff-so-fancy | less -R -+F
