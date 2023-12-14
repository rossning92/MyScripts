set -e
cd "${GIT_REPO}"

read -p 'Enter branch name: ' branch
git fetch
git switch ${branch}
