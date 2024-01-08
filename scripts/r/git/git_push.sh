set -e

# Push and auto track remote branch
git config --global push.default current

# -u:  track remote branch of the same name
git push -u
