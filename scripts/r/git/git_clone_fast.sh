set -e
mkdir -p ~/Projects/{{BRANCH}}
cd ~/Projects/{{BRANCH}}

git clone -b {{BRANCH}} --single-branch {{GIT_URL}} --single-branch --filter=blob:none .
