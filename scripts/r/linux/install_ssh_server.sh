sudo apt-get install openssh-server -y
sudo systemctl enable ssh

sudo ufw allow ssh

sudo sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config
sudo sed -zi '/AllowUsers ross/!s/$/\nAllowUsers ross/' /etc/ssh/sshd_config
sudo sed -i 's/#\?PermitRootLogin [^\n]\+/PermitRootLogin no/g' /etc/ssh/sshd_config

sudo ssh-keygen -A # generate host key if does not exist

sudo systemctl restart ssh.service
