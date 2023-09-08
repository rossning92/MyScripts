mkdir -p "${MONGODB_BACKUP_DIR}"
cd "${MONGODB_BACKUP_DIR}"

echo "Backup database \"${MONGODB_NAME}\"..."
mongodump --gzip --db=${MONGODB_NAME} --archive=${MONGODB_NAME}.gz
