set -e
et --ssh-option "Port {{SSH_PORT if SSH_PORT else 22}}" --ssh-option "StrictHostKeyChecking no" {{ET_EXTRA_ARGS}} {{SSH_USER}}@{{SSH_HOST}}:{{ET_PORT if ET_PORT else 2022}}
