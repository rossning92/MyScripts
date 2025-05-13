if [ -z "$(git status --porcelain)" ]; then
  echo "Working tree is clean."
  exit 0
fi
git diff
{{ include('r/confirm_.sh', {'MESSAGE': 'Commit all changes'}) }}
git add -A
git commit --amend --no-edit --quiet