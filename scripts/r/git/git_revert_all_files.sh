set -e
cd "${GIT_REPO}"

read -p "Confirm (y/n): " ans
if [[ "$ans" == 'y' ]]; then
    git reset --hard
fi
