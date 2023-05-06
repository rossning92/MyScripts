set -e

if [ ! -f ~/.ssh/id_rsa.pub ]; then
    ssh-keygen -t rsa -b 4096 -C "rossning92@gmail.com"
fi

clip <~/.ssh/id_rsa.pub
echo 'The key has been copied to clipboard. Please add a new key here: https://github.com/settings/ssh/new.'
read -p 'Press enter to exit...'
