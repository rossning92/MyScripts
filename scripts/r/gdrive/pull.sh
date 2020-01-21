# https://github.com/odeke-em/drive/blob/master/platform_packages.md

if ! [ -x "$(command -v drive)" ]; then
    sudo add-apt-repository ppa:twodopeshaggy/drive
    sudo apt-get update
    sudo apt-get install drive
fi

cd ~
cd /mnt/c  # WSL support

mkdir -p gdrive
cd gdrive
if [[ ! -d ".gd" ]]; then
    drive init
fi

# drive ls
drive pull {{_PATH}}
