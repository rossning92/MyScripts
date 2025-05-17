set -e
git reset -N HEAD~
git add --edit
git commit --reuse-message=ORIG_HEAD
