# https://github.com/dani-garcia/vaultwarden
set -e
docker pull vaultwarden/server:latest

container_id=$(docker ps -aq -f name=vaultwarden)
if [ -z "$container_id" ]; then
    echo "Container doesn't exist, starting a new one..."
    docker run -d --name vaultwarden -v /vw-data/:/data/ --restart unless-stopped -p 8001:80 vaultwarden/server:latest
else
    echo "Container already exists, restarting..."
    docker restart vaultwarden
fi
