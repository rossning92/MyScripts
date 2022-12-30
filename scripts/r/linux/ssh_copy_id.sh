# ssh-keygen
if [ ! -f ~/.ssh/id_rsa.pub ]; then
    ssh-keygen -t rsa
fi
ssh-copy-id {{SSH_USER}}@{{SSH_HOST}}
