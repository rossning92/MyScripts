set -e

if [[ -n "{{GIT_URL}}" ]]; then
    url="{{GIT_URL}}"
elif [[ -n "$1" ]]; then
    url="$1"
else
    echo "ERROR: git repo url is not provided."
    exit 1
fi

name=$(basename "$url")
repo="$HOME/Projects/$name"
mkdir -p "$repo"
cd "$repo"

if [[ -d '.git' ]]; then
    echo '".git" already exist, skip cloning.'
else
    extra_args=''
    if [[ -n "{{BRANCH}}" ]]; then
        extra_args+="-b {{BRANCH}}"
    fi
    echo "Cloning into $repo"
    git clone "$url" --single-branch --filter=blob:none ${extra_args} .
fi

# run_script ext/open_in_editor.py .
