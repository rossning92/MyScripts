# https://github.com/dani-garcia/vaultwarden
set -e

container_id=$(docker ps -aq -f name=vaultwarden)
if [ -z "$container_id" ]; then
    echo "Container doesn't exist, starting a new one..."
    docker run -d --name vaultwarden -v /vw-data/:/data/ --restart unless-stopped -p 8001:80 vaultwarden/server:latest

    # Enable https with caddy reverse proxy
    docker run -d \
        --name vaultwarden-proxy \
        --add-host=host.docker.internal:host-gateway \
        -p 443:443 \
        -p 80:80 \
        -v caddy_data:/data \
        -v caddy_config:/config \
        caddy:latest \
        caddy reverse-proxy --from https://localhost --to http://host.docker.internal:8001
else
    echo "Container already exists, restarting..."
    docker restart vaultwarden
fi
