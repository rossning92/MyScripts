set -e
for d in $GDRIVE_DIRS; do
    GDRIVE_DIR="$d" bash "$(dirname "$0")/sync_gdrive.sh"
done
