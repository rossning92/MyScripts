set -e
cd "${GIT_REPO}"

if [[ -n '{{BRANCH}}' ]]; then
    branch='{{BRANCH}}'
else
    read -p 'Enter branch name: ' branch
fi

git fetch origin ${branch}:refs/remotes/origin/${branch} --filter=blob:none
git checkout -b ${branch} origin/${branch}
