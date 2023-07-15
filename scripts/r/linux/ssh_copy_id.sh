# ssh-keygen
if [ ! -f ~/.ssh/id_rsa.pub ]; then
    ssh-keygen -t rsa
fi
ssh-copy-id -p {{SSH_PORT}} {{SSH_USER}}@{{SSH_HOST}}
