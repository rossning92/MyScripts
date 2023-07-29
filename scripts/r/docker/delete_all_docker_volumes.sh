read -p "Dangerous!!! Confirm?"
docker volume rm $(docker volume ls -q)
