for i in $(pacman -Qe); do
    grep "\[ALPM\] installed $i" /var/log/pacman.log
done |
    sort -ru |
    sed -e 's/\[ALPM\] installed //' -e 's/(.*$//' | fzf
