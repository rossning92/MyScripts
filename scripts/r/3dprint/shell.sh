#!/bin/bash

# env: PRINTER_3D_HOST
# env: PRINTER_3D_USER
# env: PRINTER_3D_PWD

SSH_HOST="$PRINTER_3D_HOST" \
    SSH_USER="$PRINTER_3D_USER" \
    SSH_PWD="$PRINTER_3D_PWD" \
    run_script r/linux/ssh.sh
