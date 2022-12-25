# https://hub.docker.com/r/octoprint/octoprint#enabling-webcam-support-with-docker
docker volume create octoprint
docker run -d -v octoprint:/octoprint --device /dev/ttyACM0:/dev/ttyACM0 --device /dev/video0:/dev/video0 -e ENABLE_MJPG_STREAMER=true -p 80:80 --name octoprint octoprint/octoprint
