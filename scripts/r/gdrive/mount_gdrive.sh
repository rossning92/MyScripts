set -e

source "$(dirname "$0")/_init_rclone.sh"

mkdir -p ~/gdrive-fuse
rclone mount --vfs-cache-mode full --daemon drive: ~/gdrive-fuse
