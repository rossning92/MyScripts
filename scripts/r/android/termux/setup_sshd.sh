#!/bin/bash
set -e

file_append() {
    if [[ ! -f $1 ]] || ! grep -qF -- "$2" $1; then
        echo "$2" >>$1
    fi
}

# WORKAROUND for TERMUX__USER_ID error when using xdg-open
file_append ~/.bashrc "export TERMUX__USER_ID=$(whoami)"

# ==============================
# Install SSH Server
# ==============================

# https://joeprevite.com/ssh-termux-from-computer/

pkill sshd || true

pkg install openssh -y

ssh-keygen -A
echo -e "123456\n123456" | passwd

sshd

# Check for SSH daemon logs
sleep 2
logcat -s 'sshd:*' -d | tail -n 10

file_append ~/.bashrc "sshd"

# https://stackoverflow.com/questions/13322485/how-to-get-the-primary-ip-address-of-the-local-machine-on-linux-and-os-x
ipaddr=$(ifconfig | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p')

echo "------"
echo "Please login using: \`ssh $(whoami)@$ipaddr -p 8022\` with password: 123456"
echo "------"
