set -e

cd ~/Projects/perfetto

rg -g "!BUILD" -g "!CHANGELOG" -g '!*.md' -g '!test/' -g '!systrace/' -g '!*.py' -g '!*.ts' "\bion_stat\b|IonStat" -p | less -r
