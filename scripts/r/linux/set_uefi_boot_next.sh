efibootmgr
read -p 'Set BootNext: ' ans
sudo efibootmgr -n "$ans"
