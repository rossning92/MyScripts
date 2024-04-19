for i in $(pacman -Qe); do
    grep "\[ALPM\] installed $i" /var/log/pacman.log
done |
    sort -u |
    sed -e 's/\[ALPM\] installed //' -e 's/(.*$//'
