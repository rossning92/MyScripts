# pacman -Qqe: list explicitly installed packages
# sort -ru: reverse chronological order with unique entries
# sed -e 's/\[ALPM\] installed //': remove log prefix
# sed -e 's/(.*$//': strip trailing details
pacman -Qqe | while read -r pkg; do
    grep "\[ALPM\] installed ${pkg} " /var/log/pacman.log
done |
    sort -ru |
    sed -e 's/\[ALPM\] installed //' -e 's/(.*$//' | fzf
