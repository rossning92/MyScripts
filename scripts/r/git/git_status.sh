[ -z "$(git status --short)" ] && git log -1 --pretty=oneline && git diff --stat HEAD~1 HEAD || git status --short
