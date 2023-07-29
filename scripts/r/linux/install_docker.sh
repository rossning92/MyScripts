# https://pimylifeup.com/raspberry-pi-docker/

# curl -fsSL https://get.docker.com -o get-docker.sh
# sudo sh get-docker.sh
# sudo usermod -aG docker $(whoami)
# logout

# https://docs.docker.com/engine/install/ubuntu/
set -e
set -x

# Dependencies
sudo apt update
sudo apt -y install apt-transport-https ca-certificates curl software-properties-common
sudo apt -y remove docker docker-engine docker.io containerd runc || true

# Add Docker’s official GPG key:
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add the Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu jammy stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

sudo apt update
sudo apt install -o 'Acquire::http::Proxy=socks5h://localhost:1080' docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Enable non-root users to run docker commands
sudo usermod -aG docker $(whoami)
