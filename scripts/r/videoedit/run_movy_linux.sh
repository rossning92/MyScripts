set -e

sudo npm i movy@latest -g
npm list --global --depth=0 | grep 'movy'
movy
