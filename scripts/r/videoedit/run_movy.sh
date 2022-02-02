set -e
echo "Opening $1..."

cd movy
npm install

if [ -z "$1" ]; then
    node bin/movy.js
else
    node bin/movy.js "$1"
fi
