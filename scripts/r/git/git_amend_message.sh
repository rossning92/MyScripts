{{if MESSAGE}}
git commit --amend -m "{{MESSAGE}}"
{{else}}
git commit --amend
{{end}}
