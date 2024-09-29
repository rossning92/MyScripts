{{if MESSAGE}}
git commit --amend -m "{{MESSAGE}}"
{{else}}
read -p 'Commit message: ' message
git commit --amend -m "$message"
{{end}}
