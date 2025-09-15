[ -z "$(git status --short)" ] && git log -1 --pretty=oneline && git diff --stat --name-status HEAD~1 HEAD || git status --short
