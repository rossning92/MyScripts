# https://github.com/odeke-em/drive/blob/master/platform_packages.md

if ! [ -x "$(command -v drive)" ]; then
    sudo add-apt-repository ppa:twodopeshaggy/drive -y
    sudo apt-get update
    sudo apt-get install drive -y
fi

cd ~
cd /mnt/c  # If is in WSL mode

mkdir -p gdrive
cd gdrive
if [[ ! -d ".gd" ]]; then
    drive init
fi
