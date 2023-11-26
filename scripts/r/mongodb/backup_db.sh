mkdir -p "${MONGODB_BACKUP_DIR}"
cd "${MONGODB_BACKUP_DIR}"

echo "Backup database \"${MONGODB_NAME}\"..."
ts="$(date +%Y_%m_%d_%H_%M_%S)"
mongodump --gzip --db=${MONGODB_NAME} --archive=${MONGODB_NAME}_${ts}.gz
