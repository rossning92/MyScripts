if ! test et; then
    sudo add-apt-repository ppa:jgmath2000/et -y
    sudo apt-get update
    sudo apt-get install et -y
fi

et -x -r 15037:5037 {{SSH_USER}}@{{SSH_HOST}}:8080
