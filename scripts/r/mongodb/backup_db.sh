set -e

MAX_BACKUPS=5

mkdir -p "${MONGODB_BACKUP_DIR}"
cd "${MONGODB_BACKUP_DIR}"

echo "Backup database \"${MONGODB_NAME}\"..."
ts="$(date +%Y_%m_%d_%H_%M_%S)"
mongodump --gzip --db=${MONGODB_NAME} --archive=${MONGODB_NAME}_${ts}.gz

# Delete old backups
files=($(ls -t ${MONGODB_NAME}_*.gz))
num_backups=${#files[@]}
if [[ $num_backups -gt $MAX_BACKUPS ]]; then
    num_delete=$((num_backups - $MAX_BACKUPS))
    if [[ $num_delete -gt 1 ]]; then
        echo "ERROR: too many backups to delete: $num_delete"
        exit 1
    fi
    for ((i = num_backups - 1; i >= $MAX_BACKUPS; i--)); do
        echo "Deleting old backup: ${files[$i]}"
        rm "${files[$i]}"
    done
fi
