set -e
cd "${MONGODB_BACKUP_DIR}"

echo "Restore database ${MONGODB_NAME} from ${MONGODB_NAME}.gz"
mongorestore --drop --gzip --archive=${MONGODB_NAME}.gz
