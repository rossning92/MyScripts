set -

repo=$(gh repo list --json name --template '{{range .}}{{.name}}{{"\n"}}{{end}}' | fzf)

mkdir -p ~/Projects/
cd ~/Projects/
gh repo clone "$repo"
