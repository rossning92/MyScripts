# https://github.com/odeke-em/drive/blob/master/platform_packages.md
set -e

if ! [ -x "$(command -v drive)" ]; then
    sudo add-apt-repository ppa:twodopeshaggy/drive -y
    sudo apt-get update
    sudo apt-get install drive -y
fi


if [[ -z "$GDRIVE_LOCAL_ROOT" ]]; then
    cd ~
    cd /mnt/c  # If is in WSL mode
    mkdir -p gdrive
    cd gdrive
else
    cd "$GDRIVE_LOCAL_ROOT"
fi


if [[ ! -d ".gd" ]]; then
    drive init
fi
