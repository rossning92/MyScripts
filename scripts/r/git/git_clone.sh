set -e

if [[ -n "$1" ]]; then
    url="$1"
elif [[ -n "{{GIT_URL}}" ]]; then
    url="{{GIT_URL}}"
else
    echo "ERROR: git repo url is not provided."
    exit 1
fi

name=$(basename "$url")
repo="$HOME/Projects/$name"
mkdir -p "$repo"
cd "$repo"

if [[ -d '.git' ]]; then
    echo "'${repo}/.git' already exist, skip cloning."
else
    extra_args=''
    if [[ -n "{{BRANCH}}" ]]; then
        extra_args+="-b {{BRANCH}}"
    fi
    echo "Cloning into $repo"

    git clone --filter=blob:none --recurse-submodules --single-branch ${extra_args} "$url" .
fi

# run_script ext/open_code_editor.py .
