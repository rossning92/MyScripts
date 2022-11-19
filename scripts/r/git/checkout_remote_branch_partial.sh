set -e
cd ${GIT_REPO}

read -p 'Enter branch name: ' branch

git fetch origin ${branch}:refs/remotes/origin/${branch} --filter=blob:none
git checkout -b ${branch} origin/${branch}
