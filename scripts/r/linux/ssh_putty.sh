
args="-ssh {{SSH_USER}}@{{SSH_HOST}}"
if [ ! -z "{{SSH_PWD}}" ]; then
    args+=" -pw {{SSH_PWD}}"
fi

putty $args &
