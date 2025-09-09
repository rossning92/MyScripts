[ -z "$(git status --porcelain)" ] && echo "Working tree is clean." && exit 0
# git diff
{{ include('r/git/git_diff_fancy.sh') }}
{{ include('r/confirm_.sh', {'MESSAGE': 'Commit all changes'}) }}
git add -A
git commit --amend --no-edit --quiet