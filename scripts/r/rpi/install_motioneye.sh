# https://github.com/motioneye-project/motioneye#installation
set -e

sudo apt update
sudo apt --no-install-recommends install ca-certificates curl python3 python3-pip

# Install and setup motionEye
sudo python3 -m pip install --break-system-packages --pre motioneye
sudo motioneye_init

sudo systemctl enable motioneye --now

# localhost:8765
# Username: admin
# Password: [leave blank]
