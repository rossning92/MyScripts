source _config.sh

ssh-keygen
ssh-copy-id {{SSH_USER}}@{{SSH_HOST}}
