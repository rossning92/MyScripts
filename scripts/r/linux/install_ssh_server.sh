set -e
set -x
if [[ -f "/etc/debian_version" ]]; then
    sudo apt-get install openssh-server -y
    sudo systemctl enable ssh
elif [[ -f "/etc/arch-release" ]]; then
    sudo pacman -S --noconfirm --needed openssh
    sudo systemctl enable sshd
fi

if [[ -x "$(command -v ufw)" ]]; then
    sudo ufw allow ssh
fi

sudo sed -E -i 's/#?PasswordAuthentication (yes|no)/PasswordAuthentication yes/g' /etc/ssh/sshd_config
sudo sed -zi '/AllowUsers ross/!s/$/\nAllowUsers ross/' /etc/ssh/sshd_config
sudo sed -E -i 's/#?PermitRootLogin (yes|no)/PermitRootLogin no/g' /etc/ssh/sshd_config

sudo ssh-keygen -A # generate host key if does not exist

if [[ -f "/etc/debian_version" ]]; then
    sudo systemctl restart ssh.service
elif [[ -f "/etc/arch-release" ]]; then
    sudo systemctl restart sshd.service
fi
