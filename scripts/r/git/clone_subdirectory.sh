set -e

if [[ ! -d "${GIT_REPO}" ]]; then
    mkdir -p "${GIT_REPO}"
    cd "${GIT_REPO}"

    # Start a Git repository
    git init

    # Track repository, do not enter subdirectory
    git remote add -f origin "${GIT_URL}"

    # Enable the tree check feature
    git config core.sparseCheckout true

    # Create a file in the path: .git/info/sparse-checkout
    # That is inside the hidden .git directory that was created
    # by running the command: git init
    # And inside it enter the name of the sub directory you only want to clone
    echo "${SUBDIR}" >>.git/info/sparse-checkout

    ## Download with pull, not clone
    git pull origin master --depth 1

    rm -rf .git
else
    echo "WARN: directory \"${GIT_REPO}\" already exist, skip."
fi
