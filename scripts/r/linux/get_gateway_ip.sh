gateway=$(ip r | awk '/^def/{print $3}')
echo "$gateway"
