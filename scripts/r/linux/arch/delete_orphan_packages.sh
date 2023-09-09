set -e
echo 'List orphan packages...'
pacman -Qdt

read -p '(press enter to delete...)'
sudo pacman -Rns --noconfirm $(pacman -Qdtq)
