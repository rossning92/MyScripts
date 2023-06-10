# ssh-keygen
if [ ! -f ~/.ssh/id_rsa.pub ]; then
    ssh-keygen -t rsa
fi
set -x
ssh-copy-id -p {{SSH_PORT}} {{SSH_USER}}@{{SSH_HOST}}
