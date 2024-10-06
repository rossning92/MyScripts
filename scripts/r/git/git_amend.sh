{{ include('r/git/git_status.sh') }}

read -n1 -p 'Commit all changes? (y/n) ' ans
if [[ "$ans" != 'y' ]]; then
    exit 1
fi

git add -A
git commit --amend --no-edit --quiet
