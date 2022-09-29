set -e
cd "$(dirname "$0")/movy"

echo 'build movy? (y/n)'
read -n1 ans
if [[ "$ans" == "y" ]]; then
    npm i
    npm run build
fi

node bin/movy.js
