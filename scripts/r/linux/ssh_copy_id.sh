# ssh-keygen
if [ ! -f ~/.ssh/id_rsa.pub ]; then
    ssh-keygen -t rsa
fi

echo 'Copy SSH public key to remote server...'
ssh-copy-id -o StrictHostKeyChecking=no -p {{SSH_PORT}} {{SSH_USER}}@{{SSH_HOST}}
