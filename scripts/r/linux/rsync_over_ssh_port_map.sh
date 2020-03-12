cd ~

# 1234 is the local port being mapped to remote 22
rsync -avz -e "ssh -p 1234" "{{_LOCAL_DIR}}" {{SSH_USER}}@localhost:~
