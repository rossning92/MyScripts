{{if MESSAGE}}
git commit --amend -m "{{MESSAGE}}"
{{else}}
EDITOR=nvim git commit --amend
{{end}}
