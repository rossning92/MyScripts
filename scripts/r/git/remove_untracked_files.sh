set -e
git clean -n
read -p "confirm (y/n):" ans
if [[ ans == 'y' ]]; then
    git clean -f
fi
