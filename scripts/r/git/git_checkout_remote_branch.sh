set -e
cd "${GIT_REPO}"

if [[ -n '{{BRANCH}}' ]]; then
    branch='{{BRANCH}}'
else
    read -p 'Enter branch name: ' branch
fi

# Partially fetch the branch from origin so it's faster
git fetch origin ${branch}:refs/remotes/origin/${branch} --filter=blob:none
git checkout -B ${branch} origin/${branch}
