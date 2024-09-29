# https://github.com/Jguer/yay?tab=readme-ov-file#binary

original_dir=$(pwd)
cd /tmp/
sudo pacman -S --needed --noconfirm git base-devel
git clone https://aur.archlinux.org/yay-bin.git
cd yay-bin
makepkg -si --noconfirm
cd -
rm -rf yay-bin
cd "$original_dir"
