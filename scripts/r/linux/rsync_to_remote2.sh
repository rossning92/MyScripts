cd ~

# # 1234 is the local port being mapped to remote 22
# rsync -avz -e "ssh -p 1234" "{{_LOCAL_DIR}}" {{SSH_USER}}@localhost:~
if ! [ -x "$(command -v inotifywait)" ]; then
    sudo apt-get install inotify-tools -y
fi

while
    rsync -avz "{{_LOCAL_DIR}}" {{SSH_USER}}@{{SSH_HOST}}:~
    inotifywait -r -e modify,create,delete,move "{{_LOCAL_DIR}}"
do true; done
