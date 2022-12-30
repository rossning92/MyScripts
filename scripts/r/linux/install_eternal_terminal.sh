# https://github.com/MisterTea/EternalTerminal#debian
echo "deb https://github.com/MisterTea/debian-et/raw/master/debian-source/ buster main" | sudo tee -a /etc/apt/sources.list.d/et.list
curl -sSL https://github.com/MisterTea/debian-et/raw/master/et.gpg | sudo tee /etc/apt/trusted.gpg.d/et.gpg >/dev/null
sudo apt update
sudo apt install et -y
