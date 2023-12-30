set -e

if ! [ -x "$(command -v et)" ]; then
    echo 'Installing et client...'
    sudo add-apt-repository ppa:jgmath2000/et -y
    sudo apt-get update
    sudo apt-get install et -y
fi

sudo systemctl enable et --now
