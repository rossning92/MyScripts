branch='{{BRANCH}}'

set -e

if [ -z "$1" ]; then
    echo "No argument provided"
    exit 1
fi
name=$(basename "$1")

repo="$HOME/Projects/${name}"
mkdir -p "$repo"
cd "$repo"

if [[ -d '.git' ]]; then
    echo '".git" already exist, skip cloning.'
else
    extra_args=''
    if [[ -n "${branch}" ]]; then
        extra_args+="-b ${branch}"
    fi
    echo "Cloning into $repo"
    git clone $1 --single-branch --filter=blob:none ${extra_args} .
fi

run_script ext/open_in_editor.py .
