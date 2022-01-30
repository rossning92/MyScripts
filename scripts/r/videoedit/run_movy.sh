set -e
echo "Opening $1..."

cd movy
npm install
node bin/movy.js "$1"
