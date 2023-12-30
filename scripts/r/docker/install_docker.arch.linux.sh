set -e

sudo pacman -S --noconfirm --needed docker
# NOTE: reboot is required

docker --version

sudo systemctl enable docker.socket --now

# Enable non-root users to run docker commands
sudo groupadd docker || true
sudo usermod -aG docker $(whoami)
# NOTE: log out and log back in to ensure that your group membership is re-evaluated.

sudo docker run hello-world
