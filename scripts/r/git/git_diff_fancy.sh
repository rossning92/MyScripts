#!/bin/bash
git_diff="git diff --color"
git diff-index --quiet HEAD -- && git_diff+=" HEAD~1 HEAD"
$git_diff | diff-so-fancy | less -R -+F