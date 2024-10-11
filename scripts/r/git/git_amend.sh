{{ include('r/git/git_status.sh') }}
{{ include('r/wait_for_key_.sh', {'MESSAGE': 'Commit all changes'}) }}
git add -A
git commit --amend --no-edit --quiet
