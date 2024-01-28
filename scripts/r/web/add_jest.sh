# https://jestjs.io/docs/getting-started

set -e

if [[ -z "$GIT_REPO" ]]; then
    echo 'ERROR: must provide GIT_REPO'
    exit 1
fi
mkdir -p "$GIT_REPO"
cd "$GIT_REPO"

npm init -y
npm pkg set 'scripts.test'='jest'
yarn add --dev jest

# Add TypeScript support.
# https://jestjs.io/docs/getting-started#via-ts-jest
yarn add --dev ts-jest
npx ts-jest config:init
