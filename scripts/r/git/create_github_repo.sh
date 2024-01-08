set -e

git_root=$(git rev-parse --show-toplevel)
repo="$(basename -- $git_root)"
echo "repo name: $repo"

if ! gh repo view rossning92/$repo; then
    gh repo create --private -y $repo
    git remote add origin https://github.com/rossning92/$repo.git     # in case remote "origin" url is not set
    git remote set-url origin https://github.com/rossning92/$repo.git # update the url
fi
