set -e

apt-get update

# https://github.com/motioneye-project/motioneye/wiki/Install-on-Debian-11-%28Bullseye%29

# Install motion, ffmpeg and v4l-utils
apt-get install motion ffmpeg v4l-utils -y
systemctl stop motion
systemctl disable motion

# Install the python 2.7 and pip2
apt-get install python2 curl -y
curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py
python2 get-pip.py

# Install the dependencies from the repositories
apt-get install python-dev-is-python2 python-setuptools libssl-dev libcurl4-openssl-dev libjpeg-dev zlib1g-dev libffi-dev libzbar-dev libzbar0 -y

# Install motioneye
python2 -m pip install motioneye

# Prepare the configuration directory
mkdir -p /etc/motioneye
cp /usr/local/share/motioneye/extra/motioneye.conf.sample /etc/motioneye/motioneye.conf

# Prepare the media directory
mkdir -p /var/lib/motioneye

# Add an init script, configure it to run at startup and start the motionEye server
cp /usr/local/share/motioneye/extra/motioneye.systemd-unit-local /etc/systemd/system/motioneye.service
systemctl daemon-reload
systemctl enable motioneye
systemctl start motioneye

# localhost:8765
# Username: admin
# Password: [leave blank]
