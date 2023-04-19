set -e

# repo_dir="~/Projects/{{BRANCH}}"
# echo "Clone into $repo_dir"
# mkdir -p "$repo_dir"
# cd "$repo_dir"

if [[ -d '.git' ]]; then
    echo '".git" already exist, skip cloning.'
else
    git clone -b {{BRANCH}} --single-branch {{GIT_URL}} --single-branch --filter=blob:none .
fi
