# ssh-keygen
if [ ! -f ~/.ssh/id_rsa.pub ]; then
    ssh-keygen -t rsa
fi
set -x
if ! ssh -q -o "BatchMode=yes" {SSH_USER}}@{{SSH_HOST}} exit; then
    ssh-copy-id -p {{SSH_PORT}} {{SSH_USER}}@{{SSH_HOST}}
fi
