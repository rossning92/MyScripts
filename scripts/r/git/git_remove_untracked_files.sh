set -e
cd "${GIT_REPO}"

git clean -n -x -d
read -p "Confirm (y/n): " ans
if [[ "$ans" == 'y' ]]; then
    git clean -f -x -d
fi
